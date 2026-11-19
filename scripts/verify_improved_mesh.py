import bpy
import bmesh
import numpy as np

def check_glb(path, label):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    obj = bpy.context.selected_objects[0]
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    non_manifold_e = [e for e in bm.edges if not e.is_manifold]
    boundary_e = [e for e in bm.edges if e.is_boundary]
    
    # Islands
    islands = []
    unvisited = set(bm.faces)
    while unvisited:
        start = unvisited.pop()
        island = [start]
        stack = [start]
        while stack:
            f = stack.pop()
            for e in f.edges:
                for nbr in e.link_faces:
                    if nbr in unvisited:
                        unvisited.remove(nbr)
                        island.append(nbr)
                        stack.append(nbr)
        islands.append(island)

    min_x = min(v.co.x for v in bm.verts)
    max_x = max(v.co.x for v in bm.verts)
    min_y = min(v.co.y for v in bm.verts)
    max_y = max(v.co.y for v in bm.verts)
    min_z = min(v.co.z for v in bm.verts)
    max_z = max(v.co.z for v in bm.verts)

    print(f"\n=== {label} ===")
    print(f"Verts: {len(bm.verts)}, Faces: {len(bm.faces)}")
    print(f"Non-manifold edges (excluding boundary): {len(non_manifold_e) - len(boundary_e)}")
    print(f"Boundary edges: {len(boundary_e)}")
    print(f"Connected components (islands): {len(islands)}")
    print(f"Dimensions: Width={(max_x-min_x)*100:.2f} cm, Height={(max_z-min_z)*100:.2f} cm, Depth={(max_y-min_y)*100:.2f} cm")
    print(f"X: [{min_x*100:.1f}, {max_x*100:.1f}], Y: [{min_y*100:.1f}, {max_y*100:.1f}], Z: [{min_z*100:.1f}, {max_z*100:.1f}]")

    # Shoulder top width & depth
    shoulder_verts = [v for v in bm.verts if v.co.z > max_z - 0.05]
    print(f"Shoulder top verts (Z > {max_z-0.05:.3f}): {len(shoulder_verts)}")
    ys = [v.co.y for v in shoulder_verts]
    print(f"  Shoulder top Y span: [{min(ys)*100:.1f}, {max(ys)*100:.1f}] cm (depth: {(max(ys)-min(ys))*100:.1f} cm)")

check_glb("/tmp/improved_crew_test.glb", "IMPROVED CREW NECK")
check_glb("/tmp/improved_polo_test.glb", "IMPROVED POLO")
