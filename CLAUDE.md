# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Imgr is an AI-assisted image segmentation application that uses Meta's Segment Anything Model (SAM). It's structured as a monorepo with a FastAPI backend and Svelte frontend.

## Monorepo Structure

```
backend/     # FastAPI server for SAM-based mask generation
frontend/    # Svelte + TypeScript web UI
segment-anything/  # Vendored SAM library (cloned from Meta's repo)
```

Each subdirectory has its own `CLAUDE.md` with detailed component-specific information.

## Quick Start

### Running the Full Application

1. **Backend Setup and Run**:
```bash
cd backend
uv sync

# Download SAM model (only needed once)
cd models
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
cd ..

# Start backend server
uv run uvicorn api.main:app --reload --port 8000
```
Backend runs at http://localhost:8000

2. **Frontend Setup and Run** (in a separate terminal):
```bash
cd frontend
bun install
bun run dev
```
Frontend runs at http://localhost:5173

### Development Workflow

**Backend Development**:
```bash
cd backend
uv run pytest              # Run all tests
uv run pytest tests/test_api.py  # Run specific test
```

**Frontend Development**:
```bash
cd frontend
bun run check-all          # Format, lint, and type-check
bun run format             # Format code
bun run lint:fix           # Fix linting issues
bun run type-check         # Run TypeScript checks
```

## Architecture Overview

### Communication Flow

1. User uploads an image in the frontend (Svelte UI)
2. Frontend sends image to backend `/api/upload/image` → receives `image_id`
3. User selects foreground/background points on the image
4. Frontend converts display coordinates to actual image pixel coordinates
5. Frontend sends points/labels to `/api/run` with `image_id`
6. Backend processes through service chain:
   - **SAMService**: Generates 3 candidate masks using SAM model
   - **MaskRefinementService**: Applies smoothing and feathering
   - **MaskGenerationService**: Orchestrates the pipeline
7. Backend returns 3 base64-encoded masked images + confidence scores
8. Frontend displays results in a 2x3 grid

### Technology Stack

**Backend**:
- FastAPI for REST API
- PyTorch + segment-anything for ML inference
- OpenCV for image processing and morphological operations
- uv for Python package management

**Frontend**:
- Svelte 4 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Bun for package management

### Key Design Patterns

**Backend**: Three-tier service architecture with singleton pattern
- Services are instantiated once on startup
- SAM model loads checkpoint into memory on first request
- Mask refinement algorithms are stateless and reusable

**Frontend**: Single-component application
- All state managed in `App.svelte`
- Coordinate transformation layer between display and image pixels
- Dark mode persisted to localStorage

## SAM Model Configuration

The backend supports three SAM model variants (in `backend/models/`):
- `sam_vit_h_4b8939.pth` - ViT-H (~2.4GB, default, most accurate)
- `sam_vit_l_0b3195.pth` - ViT-L (~1.2GB, balanced)
- `sam_vit_b_01ec64.pth` - ViT-B (smallest/fastest)

Set custom model via environment variable:
```bash
export SAM_CHECKPOINT_PATH=models/sam_vit_b_01ec64.pth
```

## Testing

Backend has pytest-based tests for API endpoints. Frontend currently has no tests configured.

```bash
# Backend tests
cd backend && uv run pytest -v
```

## Project Dependencies

**Backend** (`backend/pyproject.toml`):
- Python ≥3.9
- segment-anything installed from GitHub
- Uses uv for dependency management

**Frontend** (`frontend/package.json`):
- Node/Bun for package management
- TypeScript in strict mode
- ESLint 9 + Prettier for code quality

## Common Tasks

**Adding a new feathering method**:
1. Implement algorithm in `backend/api/mask_refinement_service.py`
2. Add method name to `FeatherMethod` enum in `backend/api/consts.py`
3. Update default in `FEATHER_METHOD` constant if desired
4. Test with `uv run pytest tests/test_api.py`

**Modifying the UI layout**:
1. Edit `frontend/src/App.svelte` (single-component app)
2. Use Tailwind classes for styling
3. Run `bun run check-all` before committing

**Changing coordinate handling**:
1. Modify transformation logic in `App.svelte` (search for "scale" or "actual image")
2. Ensure points are sent to backend as actual pixel coordinates (integers)
3. Test with images of different dimensions
