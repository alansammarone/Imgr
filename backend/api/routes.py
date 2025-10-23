import asyncio
import base64
import io
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from PIL import Image

router = APIRouter()

# In-memory storage for uploaded images and job status
uploaded_images: Dict[str, bytes] = {}
job_status: Dict[str, dict] = {}
job_connections: Dict[str, list] = {}


# Helper functions for mask encoding
def _get_mask_bbox(mask: np.ndarray) -> Tuple[int, int, int, int]:
    """
    Get bounding box of mask.

    Returns:
        (x_min, y_min, x_max, y_max)
    """
    rows = np.any(mask > 0, axis=1)
    cols = np.any(mask > 0, axis=0)

    if not rows.any() or not cols.any():
        # Empty mask, return full image bounds
        return 0, 0, mask.shape[1], mask.shape[0]

    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]

    return int(x_min), int(y_min), int(x_max + 1), int(y_max + 1)


def _create_masked_image(image: Image.Image, mask: np.ndarray) -> str:
    """
    Create RGBA image with mask as alpha channel, cropped to bbox.

    Args:
        image: Original PIL image
        mask: Float numpy array with values in [0, 1]

    Returns:
        Base64 encoded data URI
    """
    # Convert to RGBA
    if image.mode != "RGBA":
        image_rgba = image.convert("RGBA")
    else:
        image_rgba = image.copy()

    # Apply mask as alpha channel (scale to 0-255)
    alpha = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    image_rgba.putalpha(alpha)

    # Get bounding box and crop
    bbox = _get_mask_bbox(mask)
    cropped = image_rgba.crop(bbox)

    # Encode to base64
    return _encode_image_base64(cropped)


def _create_mask_image(mask: np.ndarray, original_size: Tuple[int, int]) -> str:
    """
    Create RGB mask image with all channels equal (full size).

    Args:
        mask: Float numpy array with values in [0, 1]
        original_size: (width, height) of original image

    Returns:
        Base64 encoded data URI
    """
    # Convert to grayscale (0-255)
    mask_gray = (mask * 255).astype(np.uint8)

    # Stack to create RGB with all channels equal
    mask_rgb = np.stack([mask_gray, mask_gray, mask_gray], axis=-1)

    # Create PIL image
    mask_image = Image.fromarray(mask_rgb, mode="RGB")

    # Ensure correct size
    if mask_image.size != original_size:
        mask_image = mask_image.resize(original_size, Image.Resampling.NEAREST)

    # Encode to base64
    return _encode_image_base64(mask_image)


def _encode_image_base64(image: Image.Image) -> str:
    """
    Encode PIL image to base64 data URI.

    Returns:
        Data URI string (data:image/png;base64,...)
    """
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    b64_string = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64_string}"


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    image_type: str = Form("original")  # "original" or "mask"
):
    """Upload an image (original or mask)"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique ID for this image
    image_id = str(uuid.uuid4())
    
    # Read and store image data
    contents = await file.read()
    uploaded_images[image_id] = contents
    
    return {
        "image_id": image_id,
        "type": image_type,
        "filename": file.filename,
        "size": len(contents)
    }


@router.post("/run")
async def run_inpainting(
    original_image_id: str = Form(...),
    mask_image_id: Optional[str] = Form(None),
    points: str = Form("[]"),
    labels: str = Form("[]")
):
    """Generate SAM masks synchronously"""
    if original_image_id not in uploaded_images:
        raise HTTPException(status_code=404, detail="Original image not found")

    if mask_image_id and mask_image_id not in uploaded_images:
        raise HTTPException(status_code=404, detail="Mask image not found")

    # Parse and validate points
    try:
        import json
        points_list = json.loads(points)
        if not isinstance(points_list, list):
            raise ValueError("Points must be a list")

        # Validate each point has x and y as integers
        for point in points_list:
            if not isinstance(point, dict) or "x" not in point or "y" not in point:
                raise ValueError("Each point must have x and y fields")
            if not isinstance(point["x"], (int, float)) or not isinstance(point["y"], (int, float)):
                raise ValueError("Point coordinates must be numeric")
            # Convert to integers
            point["x"] = int(point["x"])
            point["y"] = int(point["y"])

        # Parse and validate labels
        labels_list = json.loads(labels)
        if not isinstance(labels_list, list):
            raise ValueError("Labels must be a list")

        # Validate labels are integers (0 or 1)
        for label in labels_list:
            if not isinstance(label, int) or label not in [0, 1]:
                raise ValueError("Each label must be 0 (negative) or 1 (positive)")

        # Validate points and labels have same length
        if len(points_list) != len(labels_list):
            raise ValueError("Points and labels must have the same length")

    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid points/labels format: {str(e)}")

    # Process synchronously
    try:
        from .mask_generation_service import get_mask_generation_service

        # Get original image
        original_image_bytes = uploaded_images[original_image_id]

        # Load image
        original_image = Image.open(io.BytesIO(original_image_bytes))

        # Get mask generation service and generate refined masks
        mask_gen_service = get_mask_generation_service()

        # Run mask generation in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        raw_results = await loop.run_in_executor(
            None,
            mask_gen_service.generate_masks,
            original_image,
            points_list,
            labels_list
        )

        # Encode masks to base64 for API response
        results = []
        for result in raw_results:
            mask = result["mask"]
            score = result["score"]

            # Create masked image (cropped to bbox)
            masked_image_b64 = _create_masked_image(original_image, mask)

            # Create grayscale mask (full size)
            mask_image_b64 = _create_mask_image(mask, original_image.size)

            results.append(
                {
                    "masked_image": masked_image_b64,
                    "mask": mask_image_b64,
                    "score": score,
                }
            )

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mask generation failed: {str(e)}")


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status[job_id]


@router.websocket("/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    
    # Register this connection
    if job_id not in job_connections:
        job_connections[job_id] = []
    job_connections[job_id].append(websocket)
    
    try:
        # Keep connection alive and send updates
        while True:
            if job_id in job_status:
                await websocket.send_json(job_status[job_id])
                
                # If job is complete, close connection
                if job_status[job_id]["status"] in ["completed", "failed"]:
                    break
            
            await asyncio.sleep(0.5)
    
    except WebSocketDisconnect:
        pass
    finally:
        # Unregister connection
        if job_id in job_connections:
            job_connections[job_id].remove(websocket)
