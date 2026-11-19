import bpy
import numpy as np

# We will modify garment_builder to print armhole matching distances
import sys
import os
sys.path.insert(0, os.path.abspath("backend/blender_engine"))

# Let us load test_sleeve_audit.glb and check the mesh topology
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="storage/test_sleeve_audit.glb")
obj = bpy.context.selected_objects[0]
mesh = obj.data

# Find non-manifold edges
edges_face_count = {}
for poly in mesh.polygons:
    for e in poly.edge_keys:
        edges_face_count[e] = edges_face_count.get(e, 0) + 1

boundary_edges = [e for e, count in edges_face_count.items() if count == 1]
non_manifold_edges = [e for e, count in edges_face_count.items() if count > 2]

print("Boundary edges count (should only be at neck, hem, and sleeve cuffs):", len(boundary_edges))
print("Non-manifold edges count (should be 0!):", len(non_manifold_edges))

# Identify boundary loops
# A clean garment has exactly 4 open boundary loops:
# 1. Neck opening
# 2. Bottom hem
# 3. Right sleeve cuff
# 4. Left sleeve cuff

adj = {}
for e in boundary_edges:
    v1, v2 = e
    adj.setdefault(v1, []).append(v2)
    adj.setdefault(v2, []).append(v1)

visited = set()
loops = []
for v in adj:
    if v not in visited:
        loop = []
        curr = v
        prev = None
        while curr is not None and curr not in visited:
            visited.add(curr)
            loop.append(curr)
            neighbors = [n for n in adj[curr] if n != prev]
            if neighbors:
                prev = curr
                curr = neighbors[0]
            else:
                curr = None
        loops.append(loop)

print(f"Number of distinct boundary loops found: {len(loops)}")
for idx, loop in enumerate(loops):
    coords = [mesh.vertices[vi].co for vi in loop]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    zs = [c.z for c in coords]
    print(f"Loop {idx}: {len(loop)} verts, X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")
