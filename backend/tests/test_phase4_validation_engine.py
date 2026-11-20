"""Phase 4 Validation Engine Test Suite.
Tests automated post-deformation mesh measurement (slice circumference, shoulder span, HPS length)
with strict ±0.50 cm reporting across both Plain Crew-Neck and Polo T-Shirts.
"""
import pytest
import os
import json
from backend.services.blender_service import BlenderService
from backend.models.schemas import GarmentConfiguration, MeasurementValues
from backend.validation.garment_geometry_auditor import GarmentGeometryAuditor, TOLERANCE_CM


SIZES_MATRIX = {
    "XS":  {"chest": 94.0,  "shoulder": 43.0, "length": 66.0, "sleeve": 19.0},
    "S":   {"chest": 100.0, "shoulder": 46.0, "length": 68.0, "sleeve": 20.0},
    "M":   {"chest": 106.0, "shoulder": 49.0, "length": 71.0, "sleeve": 21.0},
    "L":   {"chest": 112.0, "shoulder": 52.0, "length": 73.0, "sleeve": 22.0},
    "XL":  {"chest": 118.0, "shoulder": 55.0, "length": 75.0, "sleeve": 23.0},
    "XXL": {"chest": 124.0, "shoulder": 58.0, "length": 77.0, "sleeve": 24.0},
}


@pytest.mark.asyncio
async def test_phase4_plain_crew_sizes_strict_tolerance():
    """Verify that Plain Crew-Neck T-Shirt achieves strict ±0.50 cm tolerance across all sizes."""
    for sz_name, sz_vals in SIZES_MATRIX.items():
        config = GarmentConfiguration(
            garment_type="basic_crew",
            selected_size=sz_name,
            fit="regular",
            unit="cm",
            measurements=MeasurementValues(
                chest=sz_vals["chest"],
                shoulder=sz_vals["shoulder"],
                length=sz_vals["length"],
                sleeve=sz_vals["sleeve"]
            )
        )
        job = await BlenderService.generate_garment(config)
        import asyncio
        for _ in range(60):
            j = BlenderService.get_job(job.job_id)
            if j and j.status in ["completed", "failed"]:
                job = j
                break
            await asyncio.sleep(0.5)

        assert job.status == "completed", f"Generation failed for Crew size {sz_name}: {job.error}"
        assert job.metadata is not None
        rep = job.metadata.accuracy_report
        assert rep is not None, f"Accuracy report missing for Crew size {sz_name}"

        # 1. Chest Circumference
        cc = rep["chest_circumference"]
        assert cc["status"] == "PASS", f"Crew {sz_name} chest failed: {cc}"
        assert cc["difference_cm"] <= TOLERANCE_CM, f"Crew {sz_name} chest diff > {TOLERANCE_CM} cm: {cc['difference_cm']}"
        assert cc["tolerance_cm"] == 0.50

        # 2. Shoulder Seam Width
        sw = rep["shoulder_width"]
        assert sw["status"] == "PASS", f"Crew {sz_name} shoulder failed: {sw}"
        assert sw["difference_cm"] <= TOLERANCE_CM, f"Crew {sz_name} shoulder diff > {TOLERANCE_CM} cm: {sw['difference_cm']}"
        assert sw["tolerance_cm"] == 0.50

        # 3. HPS Body Length
        bl = rep["body_length"]
        assert bl["status"] == "PASS", f"Crew {sz_name} length failed: {bl}"
        assert bl["difference_cm"] <= TOLERANCE_CM, f"Crew {sz_name} length diff > {TOLERANCE_CM} cm: {bl['difference_cm']}"
        assert bl["tolerance_cm"] == 0.50

        # 4. Overall Status
        assert rep.get("overall_status") == "PASS", f"Overall status failed for Crew {sz_name}"


@pytest.mark.asyncio
async def test_phase4_polo_sizes_strict_tolerance():
    """Verify that Polo T-Shirt achieves strict ±0.50 cm tolerance across all sizes."""
    for sz_name, sz_vals in SIZES_MATRIX.items():
        config = GarmentConfiguration(
            garment_type="polo",
            selected_size=sz_name,
            fit="regular",
            unit="cm",
            measurements=MeasurementValues(
                chest=sz_vals["chest"],
                shoulder=sz_vals["shoulder"],
                length=sz_vals["length"],
                sleeve=sz_vals["sleeve"]
            )
        )
        job = await BlenderService.generate_garment(config)
        import asyncio
        for _ in range(60):
            j = BlenderService.get_job(job.job_id)
            if j and j.status in ["completed", "failed"]:
                job = j
                break
            await asyncio.sleep(0.5)

        assert job.status == "completed", f"Generation failed for Polo size {sz_name}: {job.error}"
        assert job.metadata is not None
        rep = job.metadata.accuracy_report
        assert rep is not None, f"Accuracy report missing for Polo size {sz_name}"

        # 1. Chest Circumference
        cc = rep["chest_circumference"]
        assert cc["status"] == "PASS", f"Polo {sz_name} chest failed: {cc}"
        assert cc["difference_cm"] <= TOLERANCE_CM, f"Polo {sz_name} chest diff > {TOLERANCE_CM} cm: {cc['difference_cm']}"
        assert cc["tolerance_cm"] == 0.50

        # 2. Shoulder Seam Width
        sw = rep["shoulder_width"]
        assert sw["status"] == "PASS", f"Polo {sz_name} shoulder failed: {sw}"
        assert sw["difference_cm"] <= TOLERANCE_CM, f"Polo {sz_name} shoulder diff > {TOLERANCE_CM} cm: {sw['difference_cm']}"
        assert sw["tolerance_cm"] == 0.50

        # 3. HPS Body Length
        bl = rep["body_length"]
        assert bl["status"] == "PASS", f"Polo {sz_name} length failed: {bl}"
        assert bl["difference_cm"] <= TOLERANCE_CM, f"Polo {sz_name} length diff > {TOLERANCE_CM} cm: {bl['difference_cm']}"
        assert bl["tolerance_cm"] == 0.50

        # 4. Overall Status
        assert rep.get("overall_status") == "PASS", f"Overall status failed for Polo {sz_name}"


def test_markdown_report_formatting():
    """Verify that Markdown audit tables render with strict ±0.50 cm headers and PASS indicators."""
    sample_audit = {
        "overall_status": "PASS",
        "chest_circumference": {
            "input_target_cm": 106.0,
            "actual_glb_cm": 106.0,
            "difference_cm": 0.0,
            "tolerance_cm": 0.50,
            "status": "PASS"
        },
        "shoulder_width": {
            "input_target_cm": 49.0,
            "actual_glb_cm": 49.0,
            "difference_cm": 0.0,
            "tolerance_cm": 0.50,
            "status": "PASS"
        },
        "body_length": {
            "input_target_cm": 71.0,
            "actual_glb_cm": 71.0,
            "difference_cm": 0.0,
            "tolerance_cm": 0.50,
            "status": "PASS"
        },
        "sleeve_length": {
            "input_target_cm": 21.0,
            "actual_glb_cm": 21.0,
            "difference_cm": 0.0,
            "tolerance_cm": 0.50,
            "status": "PASS"
        },
        "overall_dimensions": {
            "width_cm": 85.7,
            "height_cm": 71.0,
            "depth_cm": 21.7
        },
        "mesh_topology": {
            "vertex_count": 5763,
            "polygon_count": 9968,
            "topology": "2-Manifold Polygonal Mesh"
        }
    }
    md = GarmentGeometryAuditor.generate_markdown_report(sample_audit, "Test Audit Report")
    assert "PASS (ALL TOLERANCES MET)" in md
    assert "±0.50 cm" in md
    assert "Chest Circumference" in md
    assert "Shoulder Width (Seam)" in md
    assert "Body Length (HPS-Hem)" in md
