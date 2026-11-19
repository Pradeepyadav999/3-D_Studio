import bpy
import bmesh
import math
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/.user_uploaded/media_1794982315074_31e736df.glb')

obj = bpy.context.selected_objects[0]
mesh = obj.data

print("=== FACES IN SHOULDER (abs(X) > 0.08 and Z > 0.60) ===")
shoulder_faces = []
for p in mesh.polygons:
    p_verts = [mesh.vertices[vi] for vi in p.vertices]
    avg_x = sum(v.co.x for v in p_verts) / len(p_verts)
    avg_y = sum(v.co.y for v in p_verts) / len(p_verts)
    avg_z = sum(v.co.z for v in p_verts) / len(p_verts)
    if avg_z > 0.60 and abs(avg_x) > 0.08:
        shoulder_faces.append((p, avg_x, avg_y, avg_z))

print(f"Total shoulder faces: {len(shoulder_faces)}")
# Sort by X then Z
for p, ax, ay, az in sorted(shoulder_faces, key=lambda item: (item[1] > 0, abs(item[1]), item[3])):
    print(f"Face {p.index}: center=({ax*100:5.1f}, {ay*100:5.1f}, {az*100:5.1f}) cm, norm=({p.normal.x:+.2f}, {p.normal.y:+.2f}, {p.normal.z:+.2f}), num_verts={len(p.vertices)}")

print("\n=== VERIFY SHOULDER SEAMS (faces where normal.z is high and abs(norm.y) is low) ===")
seam_faces = [f for f in shoulder_faces if f[0].normal.z > 0.5]
print(f"Seam-like faces (normal.z > 0.5): {len(seam_faces)}")
for p, ax, ay, az in seam_faces:
    print(f"  Face {p.index}: center=({ax*100:5.1f}, {ay*100:5.1f}, {az*100:5.1f}) cm, normal=({p.normal.x:+.2f}, {p.normal.y:+.2f}, {p.normal.z:+.2f})")
    for vi in p.vertices:
        v = mesh.vertices[vi]
        print(f"    Vert {vi}: ({v.co.x*100:5.1f}, {v.co.y*100:5.1f}, {v.co.z*100:5.1f})")

print("\n=== ARMHOLE / SLEEVE ATTACHMENT ===")
# Where does the torso attach to the sleeve?
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Let's check vertices with highest Z near shoulder outer edge (X ~ 18-24 cm)
outer_shoulder = [v for v in bm.verts if v.co.x > 0.18 and v.co.z > 0.60]
print(f"Outer shoulder verts count: {len(outer_shoulder)}")
for v in sorted(outer_shoulder, key=lambda v: -v.co.z):
    print(f"  Vert: ({v.co.x*100:5.1f}, {v.co.y*100:5.1f}, {v.co.z*100:5.1f}) cm, valence={len(v.link_edges)}, is_boundary={v.is_boundary}")
