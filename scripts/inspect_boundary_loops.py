import bpy
import bmesh

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/.user_uploaded/media_1794982315074_31e736df.glb')

obj = bpy.context.selected_objects[0]
bm = bmesh.new()
bm.from_mesh(obj.data)

boundary_edges = [e for e in bm.edges if e.is_boundary]
print(f"Total boundary edges: {len(boundary_edges)}")

# Group boundary edges into loops
loops = []
visited = set()
for e in boundary_edges:
    if e in visited:
        continue
    loop = [e]
    visited.add(e)
    # trace forward
    curr_v = e.verts[1]
    while True:
        next_e = None
        for edge in curr_v.link_edges:
            if edge.is_boundary and edge not in visited:
                next_e = edge
                break
        if not next_e:
            break
        loop.append(next_e)
        visited.add(next_e)
        curr_v = next_e.other_vert(curr_v)
    loops.append(loop)

print(f"Found {len(loops)} boundary loops:")
for idx, loop in enumerate(loops):
    verts = []
    for e in loop:
        for v in e.verts:
            if v not in verts:
                verts.append(v)
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zs = [v.co.z for v in verts]
    print(f"Loop {idx+1}: {len(loop)} edges, {len(verts)} verts")
    print(f"  Center: ({sum(xs)/len(xs)*100:5.1f}, {sum(ys)/len(ys)*100:5.1f}, {sum(zs)/len(zs)*100:5.1f}) cm")
    print(f"  X span: [{min(xs)*100:5.1f}, {max(xs)*100:5.1f}], Y span: [{min(ys)*100:5.1f}, {max(ys)*100:5.1f}], Z span: [{min(zs)*100:5.1f}, {max(zs)*100:5.1f}]")
