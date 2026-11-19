"""Garment Generation and Job Tracking API routes."""
from fastapi import APIRouter, HTTPException, Path
from backend.models.schemas import GarmentConfiguration, GenerationJobResponse
from backend.services.blender_service import BlenderService

router = APIRouter(prefix="/api/garments", tags=["Garment Generation"])

@router.post("/generate", response_model=GenerationJobResponse)
async def generate_garment(config: GarmentConfiguration):
    try:
        job = await BlenderService.generate_garment(config)
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed to initialize: {str(e)}")

@router.get("/jobs/{job_id}", response_model=GenerationJobResponse)
async def get_job_status(job_id: str = Path(...)):
    job = BlenderService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Generation job '{job_id}' not found.")
    return job
