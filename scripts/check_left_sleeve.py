import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="storage/test_sleeve_audit.glb")
obj = bpy.context.selected_objects[0]
mesh = obj.data

# Let us check face normals and geometry of the left sleeve
l_faces = [p for p in mesh.polygons if any(mesh.vertices[vi].co.x < -0.25 for vi in p.vertices)]
print(f"Total left sleeve faces: {len(l_faces)}")

# Check how many faces share each edge in the left sleeve
edges_count = {}
for p in l_faces:
    for e in p.edge_keys:
        edges_count[e] = edges_count.get(e, 0) + 1

open_edges = [e for e, c in edges_count.items() if c == 1]
print(f"Open edges in left sleeve: {len(open_edges)}")

# Let's check the area of left sleeve faces
areas = [p.area for p in l_faces]
print(f"Min face area: {min(areas):.6f}, max face area: {max(areas):.6f}, median: {sorted(areas)[len(areas)//2]:.6f}")

# Look at left sleeve vertex positions: are any folded or overlapping?
l_verts = [mesh.vertices[vi] for p in l_faces for vi in p.vertices]
l_verts = list({v.index: v for v in l_verts}.values())
print(f"Unique vertices in left sleeve: {len(l_verts)}")
