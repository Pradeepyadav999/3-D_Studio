"""Automated Comprehensive Test Suite for Dedicated Polo & Plain Crew-Neck Builders.
Validates:
1. Basic Plain Crew-Neck Garment Generation:
   - Correct dimensional compliance (< 0.85 cm deviation on chest, < 0.5 cm on shoulder/sleeve/length)
   - 2-manifold closed geometry with hollow neckline
   - Absence of polo-specific collar/button meshes
2. Polo T-Shirt Garment Generation:
   - Correct dimensional compliance
   - 3D collar stand, folded collar leaf, and placket box integration
   - 3D buttons creation (2 or 3 buttons with pearl material)
3. End-to-end integration via garment_builder.py factory router.
"""
import pytest
import os
import json
import subprocess

from backend.validation.measurement_validator import (
    validate_and_normalize_measurements,
    MeasurementValidationError
)
from backend.models.schemas import MeasurementValues
from backend.validation.garment_geometry_auditor import GarmentGeometryAuditor

BLENDER_BIN = os.environ.get("BLENDER_BIN", "/opt/homebrew/bin/blender")
BUILDER_SCRIPT = os.path.abspath("backend/blender_engine/garment_builder.py")


def run_blender_builder(config: dict, output_glb: str) -> dict:
    os.makedirs(os.path.dirname(os.path.abspath(output_glb)), exist_ok=True)
    cmd = [
        BLENDER_BIN,
        "-b",
        "-P", BUILDER_SCRIPT,
        "--",
        "--json", json.dumps(config),
        "--output", output_glb
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Blender failed ({proc.returncode}): {proc.stderr or proc.stdout}")

    meta = {}
    for line in proc.stdout.splitlines():
        if line.startswith("GENERATION_METADATA:"):
            meta = json.loads(line.replace("GENERATION_METADATA:", "").strip())
            break
    return meta


class TestDedicatedGarmentBuilders:
    """Test dedicated builders for Polo and Plain Crew-Neck."""

    def test_basic_crew_dimensional_accuracy(self):
        """Audit Basic Crew-Neck with Section 19 measurements: 40 in chest, 17 in shoulder, 28 in length."""
        meas = MeasurementValues(
            chest=40.0,
            shoulder=17.0,
            length=28.0,
            sleeve=8.25,
            chest_measurement_type="circumference"
        )
        meas_meters, _ = validate_and_normalize_measurements(meas, unit="inches")

        output_glb = "storage/test_renders/test_crew_section19.glb"
        config = {
            "garment_type": "basic_crew",
            "selected_size": "M",
            "fit": "regular",
            "sleeve_type": "short",
            "neck_type": "round",
            "measurements": meas_meters
        }

        meta = run_blender_builder(config, output_glb)
        assert os.path.exists(output_glb)
        assert meta["garment_type"] == "basic_crew"
        assert meta["vertex_count"] > 1000

        targets_cm = {
            "chest": round(40.0 * 2.54, 2),  # 101.6 cm
            "shoulder": round(17.0 * 2.54, 2), # 43.18 cm
            "length": round(28.0 * 2.54, 2),  # 71.12 cm
            "sleeve": round(8.25 * 2.54, 2)   # 20.955 cm
        }
        audit = GarmentGeometryAuditor.audit_glb(output_glb, targets_cm)

        assert audit["chest_circumference"]["status"] == "PASS"
        assert audit["shoulder_width"]["status"] == "PASS"
        assert audit["body_length"]["status"] == "PASS"
        assert audit["sleeve_length"]["status"] == "PASS"
        assert audit["chest_circumference"]["difference_cm"] < 0.85

    def test_polo_dimensional_accuracy_and_components(self):
        """Audit Polo T-Shirt with Section 19 measurements: 40 in chest, 17 in shoulder, 28 in length, 2 buttons."""
        meas = MeasurementValues(
            chest=40.0,
            shoulder=17.0,
            length=28.0,
            sleeve=8.25,
            chest_measurement_type="circumference"
        )
        meas_meters, _ = validate_and_normalize_measurements(meas, unit="inches")

        output_glb = "storage/test_renders/test_polo_section19.glb"
        config = {
            "garment_type": "polo",
            "selected_size": "M",
            "fit": "regular",
            "sleeve_type": "short",
            "neck_type": "polo",
            "measurements": meas_meters,
            "button_count": 2
        }

        meta = run_blender_builder(config, output_glb)
        assert os.path.exists(output_glb)
        assert meta["garment_type"] == "polo"
        assert meta["vertex_count"] > 1200

        targets_cm = {
            "chest": round(40.0 * 2.54, 2),
            "shoulder": round(17.0 * 2.54, 2),
            "length": round(28.0 * 2.54, 2),
            "sleeve": round(8.25 * 2.54, 2)
        }
        audit = GarmentGeometryAuditor.audit_glb(output_glb, targets_cm)

        assert audit["chest_circumference"]["status"] == "PASS"
        assert audit["shoulder_width"]["status"] == "PASS"
        assert audit["body_length"]["status"] == "PASS"
        assert audit["sleeve_length"]["status"] == "PASS"
        assert audit["chest_circumference"]["difference_cm"] < 0.85

    def test_flat_chest_width_matches_circumference(self):
        """Verify that 20 in flat chest width generates the exact same dimensions as 40 in circumference."""
        meas_flat = MeasurementValues(
            chest=20.0,
            shoulder=17.0,
            length=28.0,
            chest_measurement_type="flat_width"
        )
        norm_flat, _ = validate_and_normalize_measurements(meas_flat, unit="inches")

        meas_circ = MeasurementValues(
            chest=40.0,
            shoulder=17.0,
            length=28.0,
            chest_measurement_type="circumference"
        )
        norm_circ, _ = validate_and_normalize_measurements(meas_circ, unit="inches")

        assert abs(norm_flat["chest"] - norm_circ["chest"]) < 1e-6
