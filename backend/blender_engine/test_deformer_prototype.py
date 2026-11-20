import bpy
import bmesh
import math
import numpy as np

blend_path = "storage/base_models/plain_crew_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

obj = bpy.data.objects.get("PlainCrewTShirt") or [o for o in bpy.data.objects if o.type == 'MESH'][0]
mesh = obj.data

torso_vg = obj.vertex_groups['Torso'].index
torso_verts = [v for v in mesh.vertices if any(g.group == torso_vg for g in v.groups)]

# Measure circumference around z = 0.50
z_chest = 0.50
slice_verts = [v for v in torso_verts if abs(v.co.z - z_chest) < 0.04]
print(f"Slice verts count: {len(slice_verts)}")

# Let's inspect unique Z levels in torso_verts
z_levels = sorted(list({round(v.co.z, 4) for v in torso_verts}))
print(f"Torso Z levels ({len(z_levels)}):", z_levels)

# Pick underarm ring level (around 0.495)
r14_verts = [v for v in torso_verts if abs(v.co.z - 0.495) < 0.015]
print(f"Underarm ring verts: {len(r14_verts)}")

