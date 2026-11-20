import bpy
import math

blend_path = "storage/base_models/plain_crew_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)
obj = bpy.data.objects["PlainCrewTShirt"]
mesh = obj.data

torso_vg = obj.vertex_groups['Torso'].index
torso_verts = [v for v in mesh.vertices if any(g.group == torso_vg for g in v.groups)]

r14_torso = [v for v in torso_verts if abs(v.co.z - 0.495) < 0.001]
print(f"R14 torso count: {len(r14_torso)}")

tw = max(v.co.x for v in r14_torso) - min(v.co.x for v in r14_torso)
td = max(v.co.y for v in r14_torso) - min(v.co.y for v in r14_torso)
print(f"R14 torso width: {tw*100:.2f}cm, depth: {td*100:.2f}cm")

# Let's inspect the rings below 0.495
for z_check in [0.4596, 0.4243, 0.3889]:
    r_check = [v for v in torso_verts if abs(v.co.z - z_check) < 0.001]
    tw = max(v.co.x for v in r_check) - min(v.co.x for v in r_check)
    td = max(v.co.y for v in r_check) - min(v.co.y for v in r_check)
    angles = [(math.atan2(v.co.y, v.co.x), v) for v in r_check]
    angles.sort(key=lambda t: t[0])
    sorted_v = [t[1] for t in angles]
    perim = sum(math.hypot(sorted_v[(i+1)%len(sorted_v)].co.x - sorted_v[i].co.x, sorted_v[(i+1)%len(sorted_v)].co.y - sorted_v[i].co.y) for i in range(len(sorted_v)))
    print(f"Z={z_check:.4f}: count={len(r_check)}, width={tw*100:.2f}cm, depth={td*100:.2f}cm, perimeter={perim*100:.2f}cm")

