import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="storage/test_sleeve_audit.glb")
obj = bpy.context.selected_objects[0]
mesh = obj.data

l_faces = [p for p in mesh.polygons if any(mesh.vertices[vi].co.x < -0.25 for vi in p.vertices)]
edges_count = {}
for p in l_faces:
    for e in p.edge_keys:
        edges_count[e] = edges_count.get(e, 0) + 1

open_edges = [e for e, c in edges_count.items() if c == 1]
print("Listing sample open edges:")
for e in open_edges[:20]:
    v1 = mesh.vertices[e[0]].co
    v2 = mesh.vertices[e[1]].co
    print(f"Edge {e}: ({v1.x:.3f}, {v1.y:.3f}, {v1.z:.3f}) -> ({v2.x:.3f}, {v2.y:.3f}, {v2.z:.3f})")
