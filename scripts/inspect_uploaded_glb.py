import bpy
import bmesh
import math
import numpy as np

glb_path = "/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/.user_uploaded/media_1794982315074_31e736df.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb_path)

print("\n=== IMPORTED OBJECTS ===")
for obj in bpy.context.scene.objects:
    print(f"Object: {obj.name}, type: {obj.type}, dims: {obj.dimensions}")

obj = bpy.context.selected_objects[0]
mesh = obj.data

print(f"\nMesh: {mesh.name}")
print(f"Vertices: {len(mesh.vertices)}")
print(f"Polygons: {len(mesh.polygons)}")

max_z = max(v.co.z for v in mesh.vertices)
min_z = min(v.co.z for v in mesh.vertices)
height = max_z - min_z
print(f"Height range: Z in [{min_z:.4f}, {max_z:.4f}] (Total: {height*100:.2f} cm)")
print(f"Width range:  X in [{min(v.co.x for v in mesh.vertices):.4f}, {max(v.co.x for v in mesh.vertices):.4f}]")
print(f"Depth range:  Y in [{min(v.co.y for v in mesh.vertices):.4f}, {max(v.co.y for v in mesh.vertices):.4f}]")

shoulder_verts = [v for v in mesh.vertices if v.co.z > max_z - 0.15]
print(f"\nShoulder region vertices count (Z > {max_z - 0.15:.3f}): {len(shoulder_verts)}")

x_slices = np.linspace(0.05, 0.25, 9)
print("\nShoulder cross-sections (positive X side):")
for xs in x_slices:
    slice_verts = [v for v in mesh.vertices if abs(v.co.x - xs) < 0.012 and v.co.z > max_z - 0.20]
    if slice_verts:
        zs = [v.co.z for v in slice_verts]
        ys = [v.co.y for v in slice_verts]
        print(f"  X ~ {xs*100:4.1f} cm: Z in [{min(zs)*100:4.1f}, {max(zs)*100:4.1f}] cm (span: {(max(zs)-min(zs))*100:4.1f} cm), Y in [{min(ys)*100:4.1f}, {max(ys)*100:4.1f}] cm")
    else:
        print(f"  X ~ {xs*100:4.1f} cm: NO VERTICES!")

bm = bmesh.new()
bm.from_mesh(mesh)
shoulder_bm_verts = [v for v in bm.verts if v.co.z > max_z - 0.15]
non_manifold_sh = [v for v in shoulder_bm_verts if not v.is_manifold]
boundary_sh = [v for v in shoulder_bm_verts if v.is_boundary]
print(f"\nNon-manifold verts in shoulder: {len(non_manifold_sh)}")
print(f"Boundary verts in shoulder: {len(boundary_sh)}")

# Inspect the shoulder seam: where are the front and back connected at the shoulder?
# Let's find vertices with Y near 0 at Z > max_z - 0.10
ridge_verts = [v for v in mesh.vertices if abs(v.co.y) < 0.015 and v.co.z > max_z - 0.10 and abs(v.co.x) > 0.08]
print(f"\nShoulder ridge vertices count: {len(ridge_verts)}")
for v in sorted(ridge_verts, key=lambda v: (v.co.x > 0, abs(v.co.x))):
    print(f"  Ridge vert: X={v.co.x*100:5.1f} cm, Y={v.co.y*100:5.2f} cm, Z={v.co.z*100:5.1f} cm")
