import bpy
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="storage/test_sleeve_audit.glb")

obj = bpy.context.selected_objects[0]
mesh = obj.data

print("Object:", obj.name)
print("Num vertices:", len(mesh.vertices))
print("Num polygons:", len(mesh.polygons))

# Let's find vertices with x > 0.22 (right sleeve) and x < -0.22 (left sleeve)
r_verts = [v for v in mesh.vertices if v.co.x > 0.22]
l_verts = [v for v in mesh.vertices if v.co.x < -0.22]

print(f"Right sleeve region verts count: {len(r_verts)}")
print(f"Left sleeve region verts count: {len(l_verts)}")

r_xs = [v.co.x for v in r_verts]
r_ys = [v.co.y for v in r_verts]
r_zs = [v.co.z for v in r_verts]

l_xs = [v.co.x for v in l_verts]
l_ys = [v.co.y for v in l_verts]
l_zs = [v.co.z for v in l_verts]

print(f"Right bounds: X: [{min(r_xs):.4f}, {max(r_xs):.4f}], Y: [{min(r_ys):.4f}, {max(r_ys):.4f}], Z: [{min(r_zs):.4f}, {max(r_zs):.4f}]")
print(f"Left bounds:  X: [{min(l_xs):.4f}, {max(l_xs):.4f}], Y: [{min(l_ys):.4f}, {max(l_ys):.4f}], Z: [{min(l_zs):.4f}, {max(l_zs):.4f}]")

# Let's check cross section width of both sleeves at their cuffs:
r_cuff = [v for v in r_verts if v.co.x > max(r_xs) - 0.03]
l_cuff = [v for v in l_verts if v.co.x < min(l_xs) + 0.03]

print(f"Right cuff Y range: {max(v.co.y for v in r_cuff) - min(v.co.y for v in r_cuff):.4f}, Z range: {max(v.co.z for v in r_cuff) - min(v.co.z for v in r_cuff):.4f}")
print(f"Left cuff Y range:  {max(v.co.y for v in l_cuff) - min(v.co.y for v in l_cuff):.4f}, Z range: {max(v.co.z for v in l_cuff) - min(v.co.z for v in l_cuff):.4f}")

# Check polygon areas on right vs left sleeve
r_faces = [p for p in mesh.polygons if all(mesh.vertices[v_idx].co.x > 0.22 for v_idx in p.vertices)]
l_faces = [p for p in mesh.polygons if all(mesh.vertices[v_idx].co.x < -0.22 for v_idx in p.vertices)]

print(f"Right faces count: {len(r_faces)}, total area: {sum(p.area for p in r_faces):.6f}")
print(f"Left faces count:  {len(l_faces)}, total area: {sum(p.area for p in l_faces):.6f}")

# Check for degenerate or zero-area faces or inverted normals
print(f"Min right face area: {min(p.area for p in r_faces):.6f}")
print(f"Min left face area:  {min(p.area for p in l_faces):.6f}")

# Check connection between torso and left sleeve!
# Let's check faces attached to left_ah vertices
l_border_faces = [p for p in mesh.polygons if any(mesh.vertices[v_idx].co.x < -0.15 for v_idx in p.vertices) and any(mesh.vertices[v_idx].co.x >= -0.23 for v_idx in p.vertices)]
print(f"Left border faces count: {len(l_border_faces)}")
for p in l_border_faces[:10]:
    coords = [mesh.vertices[v].co for v in p.vertices]
    print(f"  Face {p.index} normal {p.normal}: {[f'({c.x:.3f},{c.y:.3f},{c.z:.3f})' for c in coords]}")
