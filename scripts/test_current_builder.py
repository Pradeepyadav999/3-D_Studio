import sys
sys.path.insert(0, '/Users/pradeepyadav/Desktop/Codiotic/GARMENT_STUDIO')
import bpy
import bmesh
from backend.blender_engine.garment_builder import build_garment

config = {
    "measurements": {
        "chest": 1.0668,
        "shoulder": 0.4572,
        "length": 0.7366,
        "sleeve": 0.2286,
        "neck_circ": 0.4318,
        "sleeve_opening": 0.3556
    },
    "garment_type": "regular_tshirt",
    "fit": "regular",
    "sleeve_type": "short",
    "neck_type": "polo",
    "selected_size": "M"
}

out_glb = "/tmp/test_garment.glb"
res = build_garment(config, out_glb)
print("Build result:", res)

obj = bpy.context.scene.objects.get("Garment_M")
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)

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

print(f'Total connected face components (islands): {len(islands)}')
for idx, island in enumerate(islands):
    verts = set()
    for f in island:
        verts.update(f.verts)
    xs = [v.co.x for v in verts]
    zs = [v.co.z for v in verts]
    print(f'Island {idx+1}: {len(island)} faces, {len(verts)} verts, X: [{min(xs)*100:.1f}, {max(xs)*100:.1f}], Z: [{min(zs)*100:.1f}, {max(zs)*100:.1f}]')
