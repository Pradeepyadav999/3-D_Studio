import bpy
import bmesh
import numpy as np
import math
import sys
import os

sys.path.insert(0, os.path.abspath("backend/blender_engine"))
from garment_builder import solve_ellipse_radii

# Let us run the exact stitching logic and check what happens to the faces
bpy.ops.wm.read_factory_settings(use_empty=True)

chest = 1.0668
shoulder = 0.4572
length = 0.7366
sleeve = 0.20955
aspect = 2.45
sleeve_opening = chest * 0.35

# Let's import build_garment and run it, but with inspection prints
from garment_builder import build_garment

res = build_garment({
    "measurements": {
        "chest": chest,
        "shoulder": shoulder,
        "length": length,
        "sleeve": sleeve
    },
    "garment_type": "regular_tshirt",
    "selected_size": "M"
}, "storage/debug_garment.glb")

print("Build completed. Now let's inspect the mesh in the scene:")
obj = bpy.context.selected_objects[0]
mesh = obj.data

print("Vertices:", len(mesh.vertices))
print("Faces:", len(mesh.polygons))

# Let's check non-manifold vertices in Blender
import bmesh
bm = bmesh.new()
bm.from_mesh(mesh)

non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
print(f"Non-manifold vertices in entire mesh: {len(non_manifold_verts)}")

boundary_verts = [v for v in bm.verts if v.is_boundary]
print(f"Boundary vertices: {len(boundary_verts)}")

# Let's inspect the boundary loops
boundary_edges = [e for e in bm.edges if e.is_boundary]
print(f"Boundary edges: {len(boundary_edges)}")

# Group boundary edges into contiguous cycles
cycles = []
unvisited = set(boundary_edges)
while unvisited:
    start_e = unvisited.pop()
    cycle = [start_e]
    # walk forward
    curr_v = start_e.verts[1]
    while True:
        next_e = None
        for cand in curr_v.link_edges:
            if cand in unvisited:
                next_e = cand
                break
        if next_e is None:
            break
        unvisited.remove(next_e)
        cycle.append(next_e)
        curr_v = next_e.other_vert(curr_v)
    cycles.append(cycle)

print(f"Total boundary cycles found: {len(cycles)}")
for i, c in enumerate(cycles):
    v_set = {v for e in c for v in e.verts}
    xs = [v.co.x for v in v_set]
    ys = [v.co.y for v in v_set]
    zs = [v.co.z for v in v_set]
    print(f"Cycle {i}: {len(c)} edges, {len(v_set)} verts. Center: ({(min(xs)+max(xs))/2:.3f}, {(min(ys)+max(ys))/2:.3f}, {(min(zs)+max(zs))/2:.3f}), Z-range: [{min(zs):.3f}, {max(zs):.3f}]")
