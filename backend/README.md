# Imgr Backend

FastAPI backend for SAM (Segment Anything Model) mask generation.

## Setup

### 1. Install Dependencies

From the backend directory:

```bash
uv sync
```

### 2. Download SAM Model

See `backend/models/README.md` for instructions on downloading SAM model checkpoints.

The default model is `sam_vit_h_4b8939.pth` (ViT-H, largest and most accurate).

## Running the Server

From the backend directory:

```bash
uv run uvicorn api.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Configuration

### SAM Model Selection

Set the `SAM_CHECKPOINT_PATH` environment variable to use a different model:

```bash
export SAM_CHECKPOINT_PATH=models/sam_vit_b_01ec64.pth
uv run uvicorn api.main:app --reload --port 8000
```

Available models:
- `sam_vit_h_4b8939.pth` - ViT-H (default, most accurate)
- `sam_vit_l_0b3195.pth` - ViT-L (good balance)
- `sam_vit_b_01ec64.pth` - ViT-B (fastest)

## API Endpoints

### POST /api/upload/image
Upload an image for processing.

**Request:**
- `file`: Image file (multipart/form-data)
- `image_type`: "original" or "mask" (default: "original")

**Response:**
```json
{
  "image_id": "uuid",
  "type": "original",
  "filename": "example.jpg",
  "size": 123456
}
```

### POST /api/run
Generate SAM masks synchronously.

**Request:**
- `original_image_id`: UUID from upload endpoint
- `points`: JSON array of {x, y} coordinates
- `labels`: JSON array of integers (1=foreground, 0=background)

**Response:**
```json
{
  "results": [
    {
      "masked_image": "data:image/png;base64,...",
      "mask": "data:image/png;base64,...",
      "score": 0.95
    }
  ]
}
```

Returns 3 candidate masks sorted by confidence score.

## Project Structure

```
backend/
├── api/
│   ├── main.py                    # FastAPI app
│   ├── routes.py                  # API endpoints
│   ├── sam_service.py             # SAM model service
│   ├── mask_generation_service.py # Mask generation orchestration
│   ├── mask_refinement_service.py # Feathering algorithms
│   └── consts.py                  # Configuration constants
├── models/                        # SAM model checkpoints
└── pyproject.toml                 # Dependencies
```
