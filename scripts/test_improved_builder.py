import bpy
import bmesh
import sys
import os

sys.path.insert(0, os.path.abspath("backend/blender_engine"))
from garment_builder import build_garment

# Generate a test model
res = build_garment({
    "measurements": {
        "chest": 1.0668,
        "shoulder": 0.4572,
        "length": 0.7366,
        "sleeve": 0.20955
    },
    "garment_type": "regular_tshirt",
    "selected_size": "M"
}, "storage/test_clean.glb")

obj = bpy.context.selected_objects[0]
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)

orphan_verts = [v for v in bm.verts if not v.link_edges]
print("Orphan verts before cleanup:", len(orphan_verts))
if orphan_verts:
    bmesh.ops.delete(bm, geom=orphan_verts, context='VERTS')
    bm.to_mesh(mesh)

non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
print("Non-manifold verts after deleting orphans:", len(non_manifold_verts))

boundary_edges = [e for e in bm.edges if e.is_boundary]
print("Boundary edges:", len(boundary_edges))
