import bpy
import math

blend_path = "storage/base_models/plain_crew_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)
obj = bpy.data.objects["PlainCrewTShirt"]
mesh = obj.data

# Target chest: 112 cm
base_chest = 104.0
target_chest = 112.0
s_c = target_chest / base_chest

# Ring 13 vertices (z = 0.4596)
r13_verts = [v for v in mesh.vertices if abs(v.co.z - 0.4596) < 0.001]
print(f"R13 count: {len(r13_verts)}")

# Deform R13
for v in r13_verts:
    v.co.x *= s_c
    v.co.y *= s_c

mesh.update()

angles = [(math.atan2(v.co.y, v.co.x), v) for v in r13_verts]
angles.sort(key=lambda t: t[0])
sorted_v = [t[1] for t in angles]
new_perim = sum(math.hypot(sorted_v[(i+1)%len(sorted_v)].co.x - sorted_v[i].co.x, sorted_v[(i+1)%len(sorted_v)].co.y - sorted_v[i].co.y) for i in range(len(sorted_v)))
print(f"R13 new perimeter: {new_perim*100:.2f} cm (Target: {target_chest} cm, diff: {abs(new_perim*100 - target_chest):.2f} cm)")

