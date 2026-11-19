"""3D Garment Studio - FastAPI Application Entry Point."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.upload import router as upload_router
from backend.api.extraction import router as extraction_router
from backend.api.garments import router as garments_router
from backend.api.models import router as models_router
from backend.api.products import router as products_router

app = FastAPI(
    title="3D Garment Studio API",
    description="Automated E-Commerce Product Analysis and Parametric 3D Garment Generation Engine",
    version="2.0.0"
)

# Enable CORS for frontend Vite dev server (e.g. localhost:5173, localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(upload_router)
app.include_router(extraction_router)
app.include_router(garments_router)
app.include_router(models_router)
app.include_router(products_router)

# Ensure storage directories exist
STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))
for sub in ["uploads", "generated_models", "previews", "textures", "sample_products"]:
    os.makedirs(os.path.join(STORAGE_DIR, sub), exist_ok=True)

# Mount /storage as static files directory
app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "3D Garment Studio Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
