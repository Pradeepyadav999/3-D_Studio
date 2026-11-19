"""Size Chart Extraction and Management API routes."""
import os
import glob
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse
from typing import Dict

from backend.models.schemas import SizeChartData, ExtractionRequest
from backend.services.ocr_service import OCRService
from backend.services.extraction_service import ExtractionService

router = APIRouter(prefix="/api/size-chart", tags=["Extraction"])

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage"))
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")

CHARTS_DB: Dict[str, SizeChartData] = {}

def find_file_for_chart(chart_id: str) -> str:
    matches = glob.glob(os.path.join(UPLOADS_DIR, f"{chart_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"No uploaded file found for chart ID '{chart_id}'.")
    return matches[0]

@router.post("/extract", response_model=SizeChartData)
async def extract_size_chart(req: ExtractionRequest):
    chart_id = req.chart_id
    file_path = find_file_for_chart(chart_id)

    try:
        # Run OCR
        ocr_result = OCRService.extract_text_and_tokens(file_path)
        # Parse measurements
        extracted_data = ExtractionService.extract_from_raw_and_tokens(
            chart_id=chart_id,
            raw_text=ocr_result["raw_text"],
            tokens=ocr_result["tokens"]
        )
        # Store in cache/database
        CHARTS_DB[chart_id] = extracted_data
        return extracted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR Extraction failed: {str(e)}")

@router.get("/{chart_id}", response_model=SizeChartData)
async def get_size_chart(chart_id: str = Path(...)):
    if chart_id in CHARTS_DB:
        return CHARTS_DB[chart_id]
    raise HTTPException(status_code=404, detail=f"Chart '{chart_id}' not found.")

@router.put("/{chart_id}", response_model=SizeChartData)
async def update_size_chart(chart_id: str, updated_chart: SizeChartData):
    if chart_id != updated_chart.chart_id:
        updated_chart.chart_id = chart_id
    CHARTS_DB[chart_id] = updated_chart
    return updated_chart

@router.get("/file/{filename}")
async def get_uploaded_file(filename: str):
    file_path = os.path.join(UPLOADS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    ext = os.path.splitext(filename)[1].lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg" if ext in [".jpg", ".jpeg"] else "application/pdf"
    return FileResponse(file_path, media_type=media_type)
