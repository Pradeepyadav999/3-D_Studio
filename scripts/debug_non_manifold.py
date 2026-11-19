import bpy
import bmesh
import sys
import os

sys.path.insert(0, os.path.abspath("backend/blender_engine"))
from garment_builder import build_garment

bpy.ops.wm.read_factory_settings(use_empty=True)

res = build_garment({
    "measurements": {
        "chest": 1.0668,
        "shoulder": 0.4572,
        "length": 0.7366,
        "sleeve": 0.20955
    },
    "garment_type": "regular_tshirt",
    "selected_size": "M"
}, "storage/debug_garment.glb")

obj = bpy.context.selected_objects[0]
bm = bmesh.new()
bm.from_mesh(obj.data)

for v in bm.verts:
    if not v.is_manifold:
        # Check why it's not manifold
        edges = v.link_edges
        faces = v.link_faces
        print(f"Non-manifold vert {v.index} at ({v.co.x:.3f}, {v.co.y:.3f}, {v.co.z:.3f}): {len(edges)} edges, {len(faces)} faces, is_boundary={v.is_boundary}")
        if len(faces) <= 1:
            print("  Single-face or zero-face vert!")
