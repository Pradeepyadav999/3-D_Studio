import bpy
import math

blend_path = "storage/base_models/plain_crew_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)
obj = bpy.data.objects["PlainCrewTShirt"]
mesh = obj.data

# Find the exact 32 vertices of underarm ring 14
r14_verts = [v for v in mesh.vertices if abs(v.co.z - 0.495) < 0.001]
print(f"R14 count: {len(r14_verts)}")

tw = max(v.co.x for v in r14_verts) - min(v.co.x for v in r14_verts)
td = max(v.co.y for v in r14_verts) - min(v.co.y for v in r14_verts)
a = tw / 2.0
b = td / 2.0
h = ((a - b)**2) / ((a + b)**2)
circ = math.pi * (a + b) * (1.0 + (3.0 * h) / (10.0 + math.sqrt(4.0 - 3.0 * h)))
print(f"R14 width: {tw*100:.2f}cm, depth: {td*100:.2f}cm, Ramanujan circ: {circ*100:.2f}cm")

# Actual polygon perimeter sum
perim = 0.0
# sort by angle around center
angles = [(math.atan2(v.co.y, v.co.x), v) for v in r14_verts]
angles.sort(key=lambda t: t[0])
sorted_v = [t[1] for t in angles]
for i in range(len(sorted_v)):
    v1 = sorted_v[i].co
    v2 = sorted_v[(i+1)%len(sorted_v)].co
    perim += math.hypot(v2.x - v1.x, v2.y - v1.y)
print(f"R14 polygon perimeter sum: {perim*100:.2f}cm")

