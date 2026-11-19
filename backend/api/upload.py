"""Upload API Route for size chart files (PNG, JPG, JPEG, PDF)."""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.models.schemas import UploadResponse

router = APIRouter(prefix="/api/size-chart", tags=["Upload"])

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage"))
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}

@router.post("/upload", response_model=UploadResponse)
async def upload_size_chart(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_chart.png"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: PNG, JPG, JPEG, PDF."
        )

    chart_id = f"chart_{uuid.uuid4().hex[:10]}"
    saved_filename = f"{chart_id}{ext}"
    dest_path = os.path.join(UPLOADS_DIR, saved_filename)

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    with open(dest_path, "wb") as f:
        f.write(contents)

    return UploadResponse(
        chart_id=chart_id,
        filename=filename,
        file_url=f"/api/size-chart/file/{saved_filename}",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents)
    )
