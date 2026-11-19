import sys
sys.path.insert(0, '/Users/pradeepyadav/Desktop/Codiotic/GARMENT_STUDIO')
import bpy
from scripts.test_improved_shoulder_builder import build_improved_garment

cfg = {
    "measurements": {
        "chest": 1.0668,
        "shoulder": 0.4572,
        "length": 0.7366,
        "sleeve": 0.20955,
        "neck_circ": 0.4318,
        "sleeve_opening": 0.3556
    },
    "garment_type": "regular_tshirt",
    "fit": "regular",
    "sleeve_type": "short",
    "neck_type": "polo",
    "selected_size": "M"
}
res_polo = build_improved_garment(cfg, "/tmp/improved_polo_test.glb")
print("Polo Build result:", res_polo)
