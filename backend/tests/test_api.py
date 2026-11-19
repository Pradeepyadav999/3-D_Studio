"""Comprehensive API and End-to-End integration tests for 3D Garment Studio."""
import os
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_upload_and_extract_flow():
    transport = ASGITransport(app=app)
    sample_img_path = "storage/sample_size_chart.png"
    assert os.path.exists(sample_img_path), "Sample size chart must exist"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Upload
        with open(sample_img_path, "rb") as f:
            files = {"file": ("test_chart.png", f, "image/png")}
            upload_resp = await ac.post("/api/size-chart/upload", files=files)
        
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        chart_id = upload_data["chart_id"]
        assert chart_id.startswith("chart_")

        # 2. Extract
        extract_resp = await ac.post("/api/size-chart/extract", json={"chart_id": chart_id})
        assert extract_resp.status_code == 200
        chart_data = extract_resp.json()
        assert chart_data["unit"] == "cm"
        assert "L" in chart_data["sizes"]
        assert chart_data["sizes"]["L"]["chest"] == 107.0
        assert chart_data["sizes"]["L"]["shoulder"] == 46.0

        # 3. Update / Edit
        chart_data["sizes"]["L"]["chest"] = 110.0
        update_resp = await ac.put(f"/api/size-chart/{chart_id}", json=chart_data)
        assert update_resp.status_code == 200
        assert update_resp.json()["sizes"]["L"]["chest"] == 110.0

@pytest.mark.asyncio
async def test_garment_generation_and_export():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "garment_type": "regular_tshirt",
            "fit": "regular",
            "sleeve_type": "short",
            "neck_type": "round",
            "selected_size": "L",
            "unit": "cm",
            "measurements": {
                "chest": 107.0,
                "shoulder": 46.0,
                "length": 71.0,
                "sleeve": 20.0
            }
        }
        gen_resp = await ac.post("/api/garments/generate", json=payload)
        assert gen_resp.status_code == 200
        job_data = gen_resp.json()
        job_id = job_data["job_id"]
        assert job_id.startswith("job_")

        # Wait for Blender generation to finish
        for _ in range(15):
            await asyncio.sleep(1.0)
            status_resp = await ac.get(f"/api/garments/jobs/{job_id}")
            assert status_resp.status_code == 200
            current_job = status_resp.json()
            if current_job["status"] in ["completed", "failed"]:
                assert current_job["status"] == "completed"
                assert current_job["model_url"] is not None
                break
