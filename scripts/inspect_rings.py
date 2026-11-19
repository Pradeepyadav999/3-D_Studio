import sys
sys.path.insert(0, '/Users/pradeepyadav/Desktop/Codiotic/GARMENT_STUDIO')
import bpy
from backend.blender_engine.garment_builder import build_garment

config = {
    "measurements": {
        "chest": 1.0668,
        "shoulder": 0.4572,
        "length": 0.7366,
        "sleeve": 0.2286,
        "neck_circ": 0.4318,
        "sleeve_opening": 0.3556
    },
    "garment_type": "regular_tshirt",
    "fit": "regular",
    "sleeve_type": "short",
    "neck_type": "round",
    "selected_size": "M"
}

out_glb = "/tmp/test_rings.glb"
build_garment(config, out_glb)

obj = bpy.context.scene.objects.get("Garment_M")
mesh = obj.data

print("\n=== RIGHT SHOULDER COLUMNS (i=2, 3, 4, 5 and i=30, 29, 28, 27) ACROSS UPPER RINGS ===")
# Let's inspect vertices near X > 0.08 and Z > 0.60
for col, name in [(2, "Col 2 (Shoulder Tip Front)"), (3, "Col 3"), (4, "Col 4"), (5, "Col 5 (HPS Front)"),
                  (27, "Col 27 (HPS Back)"), (28, "Col 28"), (29, "Col 29"), (30, "Col 30 (Shoulder Tip Back)")]:
    print(f"\n--- {name} ---")
    # In each ring, find the vertex that matches this column's angle or index
    # We can inspect the polygons to trace column rings
