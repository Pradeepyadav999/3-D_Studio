"""Models API Route for serving generated GLB files and metadata."""
import os
import json
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse, JSONResponse
from backend.models.schemas import ModelMetadata

router = APIRouter(prefix="/api/models", tags=["3D Models"])

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage"))
MODELS_DIR = os.path.join(STORAGE_DIR, "generated_models")

@router.get("/{filename}")
async def get_model_file(filename: str = Path(...)):
    # Sanitize path to prevent directory traversal
    clean_filename = os.path.basename(filename)
    file_path = os.path.join(MODELS_DIR, clean_filename)

    if not os.path.exists(file_path):
        base_models_dir = os.path.join(STORAGE_DIR, "base_models")
        base_path = os.path.join(base_models_dir, clean_filename)
        if os.path.exists(base_path):
            file_path = base_path
        else:
            raise HTTPException(status_code=404, detail=f"Model '{clean_filename}' not found.")

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Disposition": f'inline; filename="{clean_filename}"',
        "Cache-Control": "public, max-age=3600"
    }

    return FileResponse(
        file_path,
        media_type="model/gltf-binary",
        headers=headers
    )

@router.get("/{filename}/download")
async def download_model_file(filename: str = Path(...)):
    clean_filename = os.path.basename(filename)
    file_path = os.path.join(MODELS_DIR, clean_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Model '{clean_filename}' not found.")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=clean_filename
    )

@router.get("/{filename}/metadata")
async def get_model_metadata(filename: str = Path(...)):
    clean_filename = os.path.basename(filename)
    meta_path = os.path.join(MODELS_DIR, clean_filename + ".meta.json")

    if not os.path.exists(meta_path):
        # Return fallback or 404
        raise HTTPException(status_code=404, detail=f"Metadata for '{clean_filename}' not found.")

    with open(meta_path, "r") as f:
        data = json.load(f)

    return JSONResponse(content=data)
