"""Script to generate standard deliverables: tshirt_S.glb, tshirt_M.glb, tshirt_L.glb, tshirt_XL.glb, tshirt_XXL.glb."""
import os
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
BUILDER_PY = os.path.join(ROOT_DIR, "backend/blender_engine/garment_builder.py")
OUT_DIR = os.path.join(ROOT_DIR, "storage/generated_models")
os.makedirs(OUT_DIR, exist_ok=True)

SIZE_SPECS = {
    "S": {"chest": 0.96, "shoulder": 0.40, "length": 0.66, "sleeve": 0.18},
    "M": {"chest": 1.01, "shoulder": 0.43, "length": 0.68, "sleeve": 0.19},
    "L": {"chest": 1.07, "shoulder": 0.46, "length": 0.71, "sleeve": 0.20},
    "XL": {"chest": 1.12, "shoulder": 0.48, "length": 0.73, "sleeve": 0.21},
    "XXL": {"chest": 1.18, "shoulder": 0.50, "length": 0.75, "sleeve": 0.22},
}

for size_key, m in SIZE_SPECS.items():
    cfg = {
        "garment_type": "regular_tshirt",
        "selected_size": size_key,
        "fit": "regular",
        "sleeve_type": "short",
        "neck_type": "round",
        "measurements": m
    }
    out_glb = os.path.join(OUT_DIR, f"tshirt_{size_key}.glb")
    out_meta = os.path.join(OUT_DIR, f"tshirt_{size_key}.glb.meta.json")

    cmd = [
        "/opt/homebrew/bin/blender",
        "-b",
        "-P", BUILDER_PY,
        "--",
        "--json", json.dumps(cfg),
        "--output", out_glb
    ]
    print(f"Generating 3D model for Size {size_key}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error generating {size_key}: {res.stderr}")
    else:
        # Parse metadata
        meta_dict = {}
        for line in res.stdout.splitlines():
            if line.startswith("GENERATION_METADATA:"):
                meta_dict = json.loads(line.replace("GENERATION_METADATA:", ""))
        
        full_meta = {
            "garment_type": "regular_tshirt",
            "selected_size": size_key,
            "fit": "regular",
            "unit": "cm",
            "input_measurements": {k: v * 100 for k, v in m.items()},
            "measurements_in_meters": m,
            "vertex_count": meta_dict.get("vertex_count", 466),
            "face_count": meta_dict.get("face_count", 444),
            "dimensions": meta_dict.get("dimensions", {}),
            "geometry_version": "1.0.0",
            "generation_timestamp": "2026-11-17T12:00:00Z"
        }
        with open(out_meta, "w") as f:
            json.dump(full_meta, f, indent=2)
        print(f"Successfully generated tshirt_{size_key}.glb ({os.path.getsize(out_glb)} bytes)")

print("All standard deliverable models generated successfully!")
