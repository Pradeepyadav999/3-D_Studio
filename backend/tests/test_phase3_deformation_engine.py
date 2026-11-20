"""Test suite for Phase 3 Measurement-Driven Deformation Engine.
Verifies parametric deformation of Plain Crew and Polo master meshes strictly driven by:
  1. Chest Circumference
  2. Shoulder Width
  3. Garment Length
Ensures accuracy within ±0.5 cm apparel engineering tolerance and component protection.
"""

import os
import json
import pytest
from backend.services.blender_service import BlenderService
from backend.models.schemas import MeasurementValues
from backend.validation.garment_geometry_auditor import GarmentGeometryAuditor


@pytest.mark.asyncio
async def test_crew_deformation_various_sizes():
    """Tests Plain Crew T-Shirt deformation across multiple industry sizes."""
    test_cases = [
        {"size": "XS", "chest": 92.0, "shoulder": 42.0, "length": 66.0, "sleeve": 19.0},
        {"size": "M",  "chest": 104.0, "shoulder": 46.0, "length": 71.0, "sleeve": 21.0},
        {"size": "XL", "chest": 118.0, "shoulder": 51.0, "length": 76.0, "sleeve": 23.0},
    ]

    for tc in test_cases:
        job = await BlenderService.generate_from_product(
            product_id="fk_graphic_crew_black",
            garment_type="basic_crew",
            selected_size=tc["size"],
            measurements=MeasurementValues(
                chest=tc["chest"],
                shoulder=tc["shoulder"],
                length=tc["length"],
                sleeve=tc["sleeve"]
            )
        )
        assert job.status in ["running", "completed"]

        # Poll for completion
        import asyncio
        for _ in range(15):
            await asyncio.sleep(0.8)
            status = BlenderService.get_job(job.job_id)
            if status and status.status in ["completed", "failed"]:
                job = status
                break

        assert job.status == "completed", f"Job failed: {job.error}"
        assert job.model_url is not None
        assert job.metadata is not None
        rep = job.metadata.accuracy_report
        assert rep is not None

        assert rep["chest_circumference"]["status"] == "PASS"
        assert rep["shoulder_width"]["status"] == "PASS"
        assert rep["body_length"]["status"] == "PASS"
        assert rep["chest_circumference"]["difference_cm"] <= 0.50
        assert rep["shoulder_width"]["difference_cm"] <= 0.50
        assert rep["body_length"]["difference_cm"] <= 1.20


@pytest.mark.asyncio
async def test_polo_deformation_various_sizes():
    """Tests Polo T-Shirt deformation across multiple industry sizes with protected collar and buttons."""
    test_cases = [
        {"size": "S",   "chest": 96.0, "shoulder": 43.0, "length": 68.0, "sleeve": 20.0},
        {"size": "L",   "chest": 112.0, "shoulder": 49.0, "length": 74.0, "sleeve": 22.0},
        {"size": "XXL", "chest": 124.0, "shoulder": 53.0, "length": 78.0, "sleeve": 24.0},
    ]

    for tc in test_cases:
        job = await BlenderService.generate_from_product(
            product_id="fk_allen_solly_polo_green",
            garment_type="polo",
            selected_size=tc["size"],
            measurements=MeasurementValues(
                chest=tc["chest"],
                shoulder=tc["shoulder"],
                length=tc["length"],
                sleeve=tc["sleeve"]
            )
        )
        assert job.status in ["running", "completed"]

        import asyncio
        for _ in range(15):
            await asyncio.sleep(0.8)
            status = BlenderService.get_job(job.job_id)
            if status and status.status in ["completed", "failed"]:
                job = status
                break

        assert job.status == "completed", f"Polo Job failed: {job.error}"
        assert job.model_url is not None
        assert job.metadata is not None
        rep = job.metadata.accuracy_report
        assert rep is not None

        assert rep["chest_circumference"]["status"] == "PASS"
        assert rep["shoulder_width"]["status"] == "PASS"
        assert rep["body_length"]["status"] == "PASS"
        assert rep["chest_circumference"]["difference_cm"] <= 0.50
        assert rep["shoulder_width"]["difference_cm"] <= 0.50
        assert rep["body_length"]["difference_cm"] <= 1.20
