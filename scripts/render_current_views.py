import bpy
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="storage/test_sleeve_audit.glb")

obj = bpy.context.selected_objects[0]

# Add a camera
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam

# Set render resolution
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800

# Add lighting
light_data = bpy.data.lights.new(name="KeyLight", type='SUN')
light_data.energy = 4.0
light = bpy.data.objects.new(name="KeyLight", object_data=light_data)
bpy.context.collection.objects.link(light)
light.rotation_euler = (math.radians(45), math.radians(20), math.radians(45))

# Fill light
light_data2 = bpy.data.lights.new(name="FillLight", type='SUN')
light_data2.energy = 2.0
light2 = bpy.data.objects.new(name="FillLight", object_data=light_data2)
bpy.context.collection.objects.link(light2)
light2.rotation_euler = (math.radians(-30), math.radians(-40), math.radians(-135))

# Center of the garment
bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box] if hasattr(bpy, "mathutils") else [obj.matrix_world @ v.co for v in obj.data.vertices]
from mathutils import Vector
min_z = min(v.z for v in bbox)
max_z = max(v.z for v in bbox)
center_z = (min_z + max_z) / 2.0

views = {
    "front": ((0, 2.2, center_z), (math.radians(90), 0, math.radians(180))),
    "back": ((0, -2.2, center_z), (math.radians(90), 0, 0)),
    "left": ((-2.2, 0, center_z), (math.radians(90), 0, math.radians(-90))),
    "right": ((2.2, 0, center_z), (math.radians(90), 0, math.radians(90))),
    "top": ((0, 0, 2.2 + center_z), (0, 0, 0)),
    "persp": ((1.6, 1.6, center_z + 0.8), (math.radians(65), 0, math.radians(135)))
}

import os
os.makedirs("storage/renders", exist_ok=True)

for name, (pos, rot) in views.items():
    cam.location = pos
    cam.rotation_euler = rot
    bpy.context.scene.render.filepath = f"storage/renders/current_{name}.png"
    bpy.ops.render.render(write_still=True)
    print(f"Rendered storage/renders/current_{name}.png")
