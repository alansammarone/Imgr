from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router

app = FastAPI(title="Imgr API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Initialize SAM model on startup"""
    from .sam_service import get_sam_service

    print("Initializing SAM service...")
    try:
        get_sam_service()
        print("SAM service initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize SAM service: {e}")
        print("The service will attempt to initialize on first request")


@app.get("/")
async def root():
    return {"message": "Imgr API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
