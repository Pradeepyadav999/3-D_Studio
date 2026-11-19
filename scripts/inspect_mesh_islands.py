import bpy
import bmesh

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/.user_uploaded/media_1794982315074_31e736df.glb')

obj = bpy.context.selected_objects[0]
bm = bmesh.new()
bm.from_mesh(obj.data)

print(f"Total verts: {len(bm.verts)}, edges: {len(bm.edges)}, faces: {len(bm.faces)}")

# Check connected components
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

print(f"Total connected face components (islands): {len(islands)}")
for idx, island in enumerate(islands):
    verts = set()
    for f in island:
        verts.update(f.verts)
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zs = [v.co.z for v in verts]
    print(f"Island {idx+1}: {len(island)} faces, {len(verts)} verts")
    print(f"  Center: ({sum(xs)/len(xs)*100:5.1f}, {sum(ys)/len(ys)*100:5.1f}, {sum(zs)/len(zs)*100:5.1f}) cm")
    print(f"  X: [{min(xs)*100:5.1f}, {max(xs)*100:5.1f}], Y: [{min(ys)*100:5.1f}, {max(ys)*100:5.1f}], Z: [{min(zs)*100:5.1f}, {max(zs)*100:5.1f}]")
