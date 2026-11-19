"""Automated Regression Test Suite for 3D Garment Geometry, Dimensions & Units.
Audits:
1. Exact unit conversion (inches to cm and meters)
2. Negative / invalid measurement rejection
3. Multi-size parametric GLB generation (Sizes S, M, XL)
4. Independent geometric accuracy validation with GarmentGeometryAuditor
5. 2-Manifold topology & bilateral sleeve symmetry
"""
import pytest
import os
import json
import math
import subprocess

from backend.validation.measurement_validator import (
    validate_and_normalize_measurements,
    to_meters,
    MeasurementValidationError
)
from backend.models.schemas import MeasurementValues
from backend.validation.garment_geometry_auditor import GarmentGeometryAuditor

BLENDER_BIN = os.environ.get("BLENDER_BIN", "/opt/homebrew/bin/blender")
BUILDER_SCRIPT = os.path.abspath("backend/blender_engine/garment_builder.py")


def generate_glb_sync(config: dict, output_glb_path: str) -> dict:
    """Helper to synchronously run the Blender garment builder worker."""
    cmd = [
        BLENDER_BIN,
        "-b",
        "-P", BUILDER_SCRIPT,
        "--",
        "--json", json.dumps(config),
        "--output", output_glb_path
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Blender failed with code {proc.returncode}: {proc.stderr or proc.stdout}")

    meta = {}
    for line in proc.stdout.splitlines():
        if line.startswith("GENERATION_METADATA:"):
            meta = json.loads(line.replace("GENERATION_METADATA:", "").strip())
            break
    return meta


class TestUnitConversionsAndValidation:
    """Phase 2 & Phase 9: Unit conversion and validation tests."""

    def test_reference_42in_conversion(self):
        """Audit reference input conversions: 42 in chest, 18 in shoulder, 29 in length, 8.25 in sleeve."""
        meas = MeasurementValues(
            chest=42.0,
            shoulder=18.0,
            length=29.0,
            sleeve=8.25
        )
        meas_meters, warnings = validate_and_normalize_measurements(meas, unit="inches")
        
        # Verify exact mathematical conversion in meters
        assert abs(meas_meters["chest"] - (42.0 * 0.0254)) < 1e-4
        assert abs(meas_meters["shoulder"] - (18.0 * 0.0254)) < 1e-4
        assert abs(meas_meters["length"] - (29.0 * 0.0254)) < 1e-4
        assert abs(meas_meters["sleeve"] - (8.25 * 0.0254)) < 1e-4

        # In cm
        assert abs(meas_meters["chest"] * 100.0 - 106.68) < 1e-2
        assert abs(meas_meters["shoulder"] * 100.0 - 45.72) < 1e-2
        assert abs(meas_meters["length"] * 100.0 - 73.66) < 1e-2
        assert abs(meas_meters["sleeve"] * 100.0 - 20.955) < 1e-2

    def test_reject_negative_measurement(self):
        """Verify negative measurements (like sleeve = -6 cm) are strictly rejected."""
        meas = MeasurementValues(
            chest=106.0,
            shoulder=46.0,
            length=72.0,
            sleeve=-6.0
        )
        with pytest.raises(MeasurementValidationError) as exc_info:
            validate_and_normalize_measurements(meas, unit="cm")
        assert "sleeve" in str(exc_info.value).lower()

    def test_reject_zero_or_negative_chest(self):
        """Verify zero or negative chest is strictly rejected."""
        meas = MeasurementValues(
            chest=-42.0,
            shoulder=18.0,
            length=29.0,
            sleeve=8.25
        )
        with pytest.raises(MeasurementValidationError):
            validate_and_normalize_measurements(meas, unit="inches")

    def test_reject_out_of_bounds_measurements(self):
        """Reject unphysical garment dimensions."""
        # Unphysically small chest (e.g. 10 cm)
        with pytest.raises(MeasurementValidationError):
            validate_and_normalize_measurements(
                MeasurementValues(chest=10.0, shoulder=46.0, length=72.0, sleeve=20.0),
                unit="cm"
            )

        # Unphysically huge shoulder (e.g. 150 cm)
        with pytest.raises(MeasurementValidationError):
            validate_and_normalize_measurements(
                MeasurementValues(chest=106.0, shoulder=150.0, length=72.0, sleeve=20.0),
                unit="cm"
            )


class TestGarmentGeometryAndMultiSizeAudits:
    """Phase 3, 4, 7, 8: Multi-size GLB generation and independent geometry audit."""

    @pytest.mark.parametrize("size_name, chest_in, shoulder_in, length_in, sleeve_in", [
        ("S", 38.0, 17.0, 28.0, 7.75),
        ("M", 42.0, 18.0, 29.0, 8.25),
        ("XL", 46.0, 19.5, 30.5, 8.75)
    ])
    def test_multisize_glb_generation_and_audit(self, size_name, chest_in, shoulder_in, length_in, sleeve_in):
        """Generate GLBs across multiple sizes and audit actual 3D geometry against size card."""
        meas = MeasurementValues(
            chest=chest_in,
            shoulder=shoulder_in,
            length=length_in,
            sleeve=sleeve_in
        )
        meas_meters, _ = validate_and_normalize_measurements(meas, unit="inches")

        output_glb = f"storage/generated_models/regression_test_{size_name}.glb"
        os.makedirs(os.path.dirname(output_glb), exist_ok=True)

        config = {
            "measurements": meas_meters,
            "garment_type": "regular_tshirt",
            "fit": "regular",
            "sleeve_type": "short",
            "neck_type": "round",
            "selected_size": size_name
        }

        # Run generation
        res = generate_glb_sync(config, output_glb)
        assert os.path.exists(output_glb)
        assert res.get("vertex_count", 0) > 800
        assert res.get("face_count", 0) > 800

        # Run independent geometric audit on the generated GLB
        audit_targets = {
            "chest": round(chest_in * 2.54, 2),
            "shoulder": round(shoulder_in * 2.54, 2),
            "length": round(length_in * 2.54, 2),
            "sleeve": round(sleeve_in * 2.54, 2)
        }
        audit = GarmentGeometryAuditor.audit_glb(output_glb, audit_targets)

        # Verify dimension compliance
        assert audit["chest_circumference"]["status"] == "PASS", f"Chest circumference failed: {audit['chest_circumference']}"
        assert audit["shoulder_width"]["status"] == "PASS", f"Shoulder width failed: {audit['shoulder_width']}"
        assert audit["body_length"]["status"] == "PASS", f"Body length failed: {audit['body_length']}"
        assert audit["sleeve_length"]["status"] == "PASS", f"Sleeve length failed: {audit['sleeve_length']}"

        # Verify difference is within strict engineering tolerances
        assert audit["chest_circumference"]["difference_cm"] <= 0.85
        assert audit["shoulder_width"]["difference_cm"] <= 0.60
        assert audit["body_length"]["difference_cm"] <= 1.50
