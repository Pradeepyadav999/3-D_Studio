"""Automated test suite for dedicated Plain Crew and Polo 3D garment builders,
hybrid base mesh lattice deformer, and the master garment builder dispatcher.
"""
import os
import sys
import json
import pytest
import subprocess

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BLENDER_BIN = "/Applications/Blender.app/Contents/MacOS/Blender"


@pytest.mark.skipif(not os.path.exists(BLENDER_BIN), reason="Blender binary not found on macOS")
def test_crew_geometry_builder_headless(tmp_path):
    """Test standalone headless generation of Plain Crew-Neck T-Shirt."""
    output_glb = str(tmp_path / "test_crew_out.glb")
    config = {
        "garment_type": "basic_crew",
        "selected_size": "M",
        "fit": "regular",
        "base_color_hex": "#1C1C1E",
        "measurements": {
            "chest": 1.06,
            "shoulder": 0.49,
            "length": 0.71,
            "sleeve": 0.21
        }
    }

    script = f"""
import sys, os
sys.path.insert(0, '{BASE_DIR}')
from backend.blender_engine.crew_geometry_builder import build_crew_garment
meta = build_crew_garment({config}, '{output_glb}')
print('TEST_RESULT:' + str(meta['vertex_count']))
"""
    cmd = [BLENDER_BIN, "-b", "--python-expr", script]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"Blender failed: {res.stderr}"
    assert os.path.exists(output_glb), "GLB output file was not created"
    assert os.path.getsize(output_glb) > 10000, "GLB output file is suspiciously small"
    assert "TEST_RESULT:" in res.stdout


@pytest.mark.skipif(not os.path.exists(BLENDER_BIN), reason="Blender binary not found on macOS")
def test_polo_geometry_builder_headless(tmp_path):
    """Test standalone headless generation of Men's Polo T-Shirt with buttons, stand, and leaf."""
    output_glb = str(tmp_path / "test_polo_out.glb")
    config = {
        "garment_type": "polo",
        "selected_size": "L",
        "fit": "regular",
        "base_color_hex": "#1B2A4A",
        "button_count": 2,
        "button_color_hex": "#F4F4F0",
        "measurements": {
            "chest": 1.12,
            "shoulder": 0.52,
            "length": 0.73,
            "sleeve": 0.23
        }
    }

    script = f"""
import sys, os
sys.path.insert(0, '{BASE_DIR}')
from backend.blender_engine.polo_geometry_builder import build_polo_garment
meta = build_polo_garment({config}, '{output_glb}')
print('POLO_VERTS:' + str(meta['vertex_count']))
print('POLO_FACES:' + str(meta['face_count']))
"""
    cmd = [BLENDER_BIN, "-b", "--python-expr", script]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"Blender failed: {res.stderr}"
    assert os.path.exists(output_glb), "GLB output file was not created"
    assert os.path.getsize(output_glb) > 15000, "GLB output file is suspiciously small"
    assert "POLO_VERTS:" in res.stdout
    assert "POLO_FACES:" in res.stdout


@pytest.mark.skipif(not os.path.exists(BLENDER_BIN), reason="Blender binary not found on macOS")
def test_garment_builder_dispatcher_cli(tmp_path):
    """Test garment_builder.py CLI dispatcher executing headless worker."""
    output_glb = str(tmp_path / "test_dispatcher_out.glb")
    config_dict = {
        "garment_type": "polo",
        "selected_size": "M",
        "fit": "regular",
        "base_color_hex": "#2B2D42",
        "measurements": {
            "chest": 1.06,
            "shoulder": 0.49,
            "length": 0.71,
            "sleeve": 0.22
        }
    }
    builder_py = os.path.join(BASE_DIR, "backend", "blender_engine", "garment_builder.py")

    cmd = [
        BLENDER_BIN, "-b", "-P", builder_py,
        "--",
        "--json", json.dumps(config_dict),
        "--output", output_glb
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"Dispatcher failed: {res.stderr}"
    assert os.path.exists(output_glb), "Dispatcher did not produce output GLB"
    assert "GENERATION_METADATA:" in res.stdout


@pytest.mark.skipif(not os.path.exists(BLENDER_BIN), reason="Blender binary not found on macOS")
def test_hybrid_base_mesh_lattice_deformer(tmp_path):
    """Test hybrid base mesh deformation engine scaling canonical model to custom measurements."""
    base_glb = os.path.join(BASE_DIR, "storage", "base_models", "crew_master_base.glb")
    if not os.path.exists(base_glb):
        pytest.skip("Base model crew_master_base.glb not yet generated")

    output_glb = str(tmp_path / "test_deformed_out.glb")
    custom_meas = {
        "chest": 1.18,      # XL chest (46.5 in)
        "shoulder": 0.54,   # XL shoulder (21.2 in)
        "length": 0.76,     # XL length (30 in)
        "sleeve": 0.24
    }
    config = {
        "garment_type": "basic_crew",
        "base_color_hex": "#334155"
    }

    script = f"""
import sys, os
sys.path.insert(0, '{BASE_DIR}')
from backend.blender_engine.lattice_deformer import deform_base_garment
meta = deform_base_garment('{base_glb}', {custom_meas}, {config}, '{output_glb}')
print('DEFORMED_HEIGHT:' + str(meta['dimensions']['height_m']))
"""
    cmd = [BLENDER_BIN, "-b", "--python-expr", script]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"Deformer failed: {res.stderr}"
    assert os.path.exists(output_glb), "Deformed GLB was not created"
    assert "DEFORMED_HEIGHT:" in res.stdout
