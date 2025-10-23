"""SAM (Segment Anything Model) service for mask generation."""

import os
from typing import Dict, List

import cv2
import numpy as np
from PIL import Image
from segment_anything import SamPredictor, sam_model_registry


class SAMService:
    """Singleton service for SAM model."""

    _instance = None
    _predictor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize SAM model if not already initialized."""
        if self._predictor is None:
            self._initialize_model()

    def _initialize_model(self):
        """Load SAM model from checkpoint."""
        from pathlib import Path

        # Get checkpoint path - default to backend/models/sam_vit_b_01ec64.pth
        backend_dir = Path(__file__).parent.parent
        default_checkpoint = backend_dir / "models" / "sam_vit_h_4b8939.pth"
        sam_checkpoint = os.environ.get("SAM_CHECKPOINT_PATH", str(default_checkpoint))
        model_type = "vit_h"

        # Use CPU device (MPS has issues with this library)
        device = "cpu"

        print(f"Loading SAM model from {sam_checkpoint} on device: {device}")

        # Load model
        sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
        sam.to(device=device)

        # Create predictor
        self._predictor = SamPredictor(sam)

        print("SAM model loaded successfully")

    def generate_masks(
        self, image: Image.Image, points: List[Dict[str, int]], labels: List[int]
    ) -> List[Dict[str, any]]:
        """
        Generate 3 candidate masks for given image and points.

        Args:
            image: PIL Image (RGB)
            points: List of dicts with 'x' and 'y' keys
            labels: List of ints (1 for positive/foreground, 0 for negative/background)

        Returns:
            List of dicts containing:
                - mask: numpy boolean array (H, W)
                - score: float confidence score
        """
        # Convert PIL to numpy RGB
        image_np = np.array(image)

        # Ensure RGB format
        if len(image_np.shape) == 2:  # Grayscale
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
        elif image_np.shape[2] == 4:  # RGBA
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)

        # Set image for predictor (calculates embeddings)
        self._predictor.set_image(image_np)

        # Prepare points for SAM
        input_points = np.array([[p["x"], p["y"]] for p in points])
        input_labels = np.array(labels, dtype=np.int32)  # Use provided labels (1=foreground, 0=background)

        # Generate masks
        masks, scores, logits = self._predictor.predict(
            point_coords=input_points,
            point_labels=input_labels,
            multimask_output=True,  # Generate 3 candidate masks
        )

        # Sort by score (highest first)
        sorted_indices = np.argsort(scores)[::-1]

        # Process each mask
        results = []
        for idx in sorted_indices:
            mask = masks[idx]
            score = float(scores[idx])

            # Threshold mask to ensure strictly binary values (0.0 or 1.0)
            # Threshold at midpoint (0.5) to handle any non-binary values
            mask = (mask > 0.5).astype(np.float32)

            results.append(
                {
                    "mask": mask,  # Return binary numpy array (0.0 or 1.0)
                    "score": score,
                }
            )

        return results


# Global singleton instance
_sam_service = None


def get_sam_service() -> SAMService:
    """Get or create the global SAM service instance."""
    global _sam_service
    if _sam_service is None:
        _sam_service = SAMService()
    return _sam_service
