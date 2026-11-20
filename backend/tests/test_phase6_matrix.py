"""Phase 6 Test Suite: Full Size-Matrix Testing across XS through 4XL.
Validates:
1. All 8 sizes for Plain Crew-Neck T-Shirt (XS, S, M, L, XL, XXL, 3XL, 4XL)
2. All 8 sizes for Polo T-Shirt (XS, S, M, L, XL, XXL, 3XL, 4XL)
3. Strict ±0.50 cm measurement tolerance on Chest, Shoulder, and Length
4. Multi-angle verification renders existence and non-zero byte size
"""
import pytest
import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MODELS_DIR = os.path.join(PROJECT_ROOT, "storage/generated_models")
RENDERS_DIR = os.path.join(PROJECT_ROOT, "verification_renders")
SUMMARY_PATH = os.path.join(RENDERS_DIR, "phase6_audit_summary.json")

SIZES = ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"]
GARMENTS = ["plain_crew", "polo"]


def test_phase6_summary_file_exists():
    assert os.path.exists(SUMMARY_PATH), f"Summary audit file missing: {SUMMARY_PATH}"
    with open(SUMMARY_PATH, "r") as f:
        data = json.load(f)
    assert "plain_crew" in data
    assert "polo" in data


@pytest.mark.parametrize("garment_type", GARMENTS)
@pytest.mark.parametrize("size", SIZES)
def test_garment_size_measurement_tolerances(garment_type, size):
    assert os.path.exists(SUMMARY_PATH)
    with open(SUMMARY_PATH, "r") as f:
        data = json.load(f)

    audit = data[garment_type][size]
    assert audit["overall_status"] == "PASS", f"Size {size} {garment_type} failed audit: {audit}"

    # Tolerance strictly <= 0.50 cm
    assert audit["chest_circumference"]["difference_cm"] <= 0.50
    assert audit["shoulder_width"]["difference_cm"] <= 0.50
    assert audit["body_length"]["difference_cm"] <= 0.50


@pytest.mark.parametrize("garment_type", GARMENTS)
@pytest.mark.parametrize("size", SIZES)
def test_generated_glb_files_exist_and_valid(garment_type, size):
    glb_path = os.path.join(MODELS_DIR, f"phase6_{garment_type}_{size}.glb")
    assert os.path.exists(glb_path), f"GLB file missing: {glb_path}"
    file_size = os.path.getsize(glb_path)
    assert file_size > 10000, f"GLB file suspiciously small ({file_size} bytes): {glb_path}"


@pytest.mark.parametrize("garment_type", GARMENTS)
@pytest.mark.parametrize("size", ["XS", "M", "4XL"])
@pytest.mark.parametrize("angle", ["front", "top", "side", "back", "collar_zoom"])
def test_verification_renders_exist(garment_type, size, angle):
    render_file = os.path.join(RENDERS_DIR, f"phase6_{garment_type}_{size}_{angle}.png")
    assert os.path.exists(render_file), f"Render missing: {render_file}"
    assert os.path.getsize(render_file) > 5000, f"Render too small: {render_file}"
