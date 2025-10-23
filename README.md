# Imgr

AI-assisted image generation web application.

## Quick Start

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Download SAM model (see backend/models/README.md)
cd models
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
cd ..

# Run server
uv run uvicorn api.main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### Frontend

```bash
cd frontend

# Install dependencies
bun install

# Run dev server
bun run dev
```

Frontend runs at http://localhost:5173

## Project Structure

```
backend/    # FastAPI server
frontend/   # Svelte web UI
```
