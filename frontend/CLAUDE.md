# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the frontend for Imgr, an AI-assisted image segmentation application using SAM (Segment Anything Model). It's a Svelte + TypeScript + Vite application that communicates with a FastAPI backend.

## Development Commands

### Setup
```bash
bun install
```

### Development Server
```bash
bun run dev
```
Runs at http://localhost:5173

### Build
```bash
bun run build
```

### Code Quality
```bash
# Format code
bun run format

# Check formatting
bun run format:check

# Lint
bun run lint

# Lint with auto-fix
bun run lint:fix

# Type check
bun run type-check

# Run all checks (format, lint, type-check)
bun run check-all
```

### Testing
There are currently no tests configured for the frontend.

## Backend Integration

The frontend expects the backend API to be running at `http://localhost:8000/api`. To run the backend:

```bash
cd ../backend
uv sync
uv run uvicorn api.main:app --reload --port 8000
```

The backend must have the SAM model downloaded to `backend/models/` (see backend README).

## Architecture

### Main Application (src/App.svelte)
The entire application is contained in a single Svelte component that handles:

1. **Image Upload**: Drag-and-drop interface for uploading images
2. **Point Selection**: Interactive point selection on images
   - Left-click: Add positive (foreground) points (blue)
   - Right-click: Add negative (background) points (red)
   - ESC key: Clear all points
3. **Coordinate Transformation**: Converts display coordinates to actual image pixel coordinates, accounting for image scaling
4. **API Communication**: Uploads images and sends point/label data to backend
5. **Results Display**: Shows 3 candidate masks in a 2x3 grid (top row: masked images, bottom row: grayscale masks)
6. **Dark Mode**: Persisted to localStorage

### API Integration Flow
1. User drops an image → stored in component state
2. User clicks points on image → stored as {x, y, label} array with actual pixel coordinates
3. User clicks "Run" → uploads image to `/api/upload/image`
4. Frontend sends POST to `/api/run` with:
   - `original_image_id`: UUID from upload
   - `points`: JSON array of {x, y} coordinates
   - `labels`: JSON array of 1 (foreground) or 0 (background)
5. Backend returns 3 results with `masked_image`, `mask`, and `score` (base64-encoded PNGs)

### Key Technical Details

- **Image Dimensions**: Tracks both display size and actual image dimensions for accurate coordinate transformation
- **Coordinate System**: Converts mouse click coordinates from display pixels to actual image pixels using scale factors
- **Point Storage**: Points stored with actual pixel coordinates (integers), not display coordinates
- **Results Format**: Backend returns base64 data URIs that can be directly used in `<img>` src attributes

## Tech Stack

- **Framework**: Svelte 4 with TypeScript
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3.4
- **Package Manager**: Bun
- **Linting**: ESLint 9 with TypeScript and Svelte plugins
- **Formatting**: Prettier with Svelte plugin

## Development Notes

- This uses Vite + Svelte (not SvelteKit) for a simpler, single-page application
- TypeScript is configured with strict mode enabled
- Dark mode state is persisted to localStorage and applied via Tailwind's `dark:` classes
- The application uses a 30/70 split layout (upload/controls on left, results on right)
