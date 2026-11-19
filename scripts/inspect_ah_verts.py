import sys
sys.path.insert(0, '/Users/pradeepyadav/Desktop/Codiotic/GARMENT_STUDIO')
import bpy
import bmesh
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

out_glb = "/tmp/test_inspect_ah.glb"
build_garment(config, out_glb)

obj = bpy.context.scene.objects.get("Garment_M")
mesh = obj.data

print("\n=== INSPECT TORSO AND SLEEVE GEOMETRY IN CURRENT BUILD ===")
# Let's inspect vertices where X > 0.15 and Z > 0.50
verts = [v for v in mesh.vertices if v.co.x > 0.15 and v.co.z > 0.50]
print(f"Total verts in right upper region: {len(verts)}")
for v in sorted(verts, key=lambda v: (-v.co.z, v.co.x)):
    print(f"  V{v.index:4d}: X={v.co.x*100:5.1f} cm, Y={v.co.y*100:5.2f} cm, Z={v.co.z*100:5.1f} cm")
