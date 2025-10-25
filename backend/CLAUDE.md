# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend for SAM (Segment Anything Model) mask generation. The API accepts user input points on images and returns multiple candidate masks with confidence scores, applying feathering/smoothing for better visual quality.

## Development Commands

### Setup
```bash
# Install dependencies (uses uv package manager)
uv sync
```

### Running the Server
```bash
# Start development server with auto-reload
uv run uvicorn api.main:app --reload --port 8000

# With custom SAM model
export SAM_CHECKPOINT_PATH=models/sam_vit_b_01ec64.pth
uv run uvicorn api.main:app --reload --port 8000
```

Server endpoints:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_api.py

# Run with verbose output
uv run pytest -v
```

## Architecture

### Service Layer (Singleton Pattern)

The application uses a three-tier service architecture with singleton instances:

1. **SAMService** (`api/sam_service.py`): Core ML model wrapper
   - Loads SAM model checkpoint on startup (default: `sam_vit_h_4b8939.pth`)
   - Generates 3 candidate masks with confidence scores using point prompts
   - Returns binary masks (0.0 or 1.0 values)
   - Uses CPU device (MPS has compatibility issues)

2. **MaskRefinementService** (`api/mask_refinement_service.py`): Post-processing algorithms
   - Applies morphological smoothing (open-close operations) to remove noise
   - Implements 7 feathering methods (linear, exponential, cosine, sigmoid, ease-out variants)
   - Uses distance transform for gradient-based edge feathering
   - Returns float masks with values in [0, 1]

3. **MaskGenerationService** (`api/mask_generation_service.py`): Orchestration layer
   - Coordinates SAMService and MaskRefinementService
   - Applies feathering configuration from `api/consts.py`
   - Current defaults: `EASE_OUT_POWER` method with 10px width

### Configuration

Global feathering settings in `api/consts.py`:
- `FEATHER_METHOD`: Which feathering algorithm to use
- `FEATHER_WIDTH`: Edge gradient width in pixels

### API Flow

1. Client uploads image via `/api/upload/image` → receives `image_id`
2. Client sends points/labels to `/api/run` with `image_id`
3. Server flow: SAMService → MaskRefinementService → Base64 encoded response
4. Returns 3 masks sorted by confidence score (highest first)

## SAM Model Setup

Models must be downloaded manually to `models/` directory:

```bash
cd models
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
```

Available models (in order of accuracy/size):
- `sam_vit_h_4b8939.pth` - ViT-H (~2.4GB, default)
- `sam_vit_l_0b3195.pth` - ViT-L (~1.2GB)
- `sam_vit_b_01ec64.pth` - ViT-B (smallest/fastest)

## Key Dependencies

- **FastAPI**: Web framework with auto-generated OpenAPI docs
- **segment-anything**: Meta's SAM library (installed from GitHub)
- **torch/torchvision**: PyTorch for SAM model inference
- **opencv-python**: Morphological operations and image processing
- **scipy**: Distance transform for feathering algorithms
- **Pillow**: Image I/O and format conversion
