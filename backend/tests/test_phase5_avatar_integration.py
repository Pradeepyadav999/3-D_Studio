"""Phase 5: Avatar Mode Integration Test Suite.
Tests avatar collision proxy generation, dimensional scaling, and collision clearance alignment.
"""
import pytest
import os
import json
import subprocess


SIZES_MATRIX = {
    "XS":  {"chest": 94.0,  "shoulder": 43.0, "length": 66.0},
    "S":   {"chest": 100.0, "shoulder": 46.0, "length": 68.0},
    "M":   {"chest": 106.0, "shoulder": 49.0, "length": 71.0},
    "L":   {"chest": 112.0, "shoulder": 52.0, "length": 73.0},
    "XL":  {"chest": 118.0, "shoulder": 55.0, "length": 75.0},
    "XXL": {"chest": 124.0, "shoulder": 58.0, "length": 77.0},
}


def test_avatar_collision_proxy_sizes_clearance():
    """Verify that avatar collision proxy maintains positive clearance without penetration across all sizes."""
    blender_bin = os.environ.get("BLENDER_BIN", "/opt/homebrew/bin/blender")
    script_path = os.path.abspath("backend/blender_engine/avatar_collision_proxy.py")

    for sz_name, sz_vals in SIZES_MATRIX.items():
        out_glb = f"/tmp/test_avatar_{sz_name}.glb"
        cmd = [
            blender_bin, "-b", "-P", script_path,
            "--",
            "--json", json.dumps({"measurements": sz_vals}),
            "--output", out_glb
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"Blender avatar proxy failed for {sz_name}: {proc.stderr}"

        res_json = None
        for line in proc.stdout.splitlines():
            if line.startswith("AVATAR_PROXY_RESULT:"):
                res_json = line.replace("AVATAR_PROXY_RESULT:", "").strip()
                break
        
        assert res_json is not None, f"No result JSON for {sz_name}"
        res = json.loads(res_json)

        assert res["status"] == "PASS", f"Avatar generation failed for {sz_name}"
        assert res["penetration_detected"] is False, f"Penetration detected for {sz_name}"
        
        # Verify positive clearance margins
        clr = res["collision_clearance_cm"]
        assert clr["radial_torso_clearance"] >= 0.50, f"Insufficient radial torso clearance for {sz_name}: {clr}"
        assert clr["shoulder_acromion_clearance"] >= 0.80, f"Insufficient shoulder clearance for {sz_name}: {clr}"
        assert clr["min_penetration_clearance"] >= 0.50, f"Min clearance too small for {sz_name}: {clr}"

        # Verify exported GLB exists and is valid
        assert os.path.exists(out_glb)
        assert os.path.getsize(out_glb) > 10000


def test_master_avatar_asset_exists():
    """Verify that master avatar proxy asset exists in storage and public directories."""
    storage_path = "storage/base_models/avatar_mannequin_proxy.glb"
    public_path = "frontend/public/avatar_mannequin_proxy.glb"

    assert os.path.exists(storage_path), f"Missing storage avatar asset: {storage_path}"
    assert os.path.exists(public_path), f"Missing public avatar asset: {public_path}"
    assert os.path.getsize(storage_path) > 10000
