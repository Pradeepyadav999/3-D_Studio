import sys
import os
import json

sys.path.insert(0, os.path.abspath("backend/blender_engine"))
from garment_builder import build_garment

config = {
    "measurements": {
        "chest": 1.0668,
        "shoulder": 0.4572,
        "length": 0.7366,
        "sleeve": 0.20955
    },
    "garment_type": "regular_tshirt",
    "fit": "regular",
    "sleeve_type": "short",
    "neck_type": "round",
    "selected_size": "M"
}

out_path = "storage/test_sleeve_audit.glb"
res = build_garment(config, out_path)
print("Generation finished:", res)
