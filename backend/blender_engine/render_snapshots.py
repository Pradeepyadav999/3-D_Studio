import bpy
import math
import sys
import os

# Parse args after --
argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = []

glb_path = args[0]
out_dir = args[1]
prefix = args[2]

os.makedirs(out_dir, exist_ok=True)

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import GLB
bpy.ops.import_scene.gltf(filepath=glb_path)

# Set render settings (Eevee / Workbench for high quality clean snapshot)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.render.resolution_x = 1000
scene.render.resolution_y = 1200
scene.render.film_transparent = False

# World background
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.92, 0.92, 0.92, 1.0) # clean light grey background like Pacdora
    bg_node.inputs[1].default_value = 1.0

# Add 3-point Studio Lighting
# Key light
key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
key_data.energy = 350
key_data.size = 1.5
key_obj = bpy.data.objects.new(name="KeyLight", object_data=key_data)
scene.collection.objects.link(key_obj)
key_obj.location = (1.2, -1.8, 1.4)
key_obj.rotation_euler = (math.radians(55), 0, math.radians(35))

# Fill light
fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
fill_data.energy = 180
fill_data.size = 2.0
fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = (-1.5, -1.5, 1.0)
fill_obj.rotation_euler = (math.radians(50), 0, math.radians(-40))

# Rim light (Backlight for silhouette definition)
rim_data = bpy.data.lights.new(name="RimLight", type='AREA')
rim_data.energy = 220
rim_data.size = 1.2
rim_obj = bpy.data.objects.new(name="RimLight", object_data=rim_data)
scene.collection.objects.link(rim_obj)
rim_obj.location = (0.0, 1.8, 1.2)
rim_obj.rotation_euler = (math.radians(130), 0, 0)

# Camera
cam_data = bpy.data.cameras.new(name="Camera")
cam_data.lens = 75 # Natural portrait focal length to avoid wide-angle distortion
cam_obj = bpy.data.objects.new(name="Camera", object_data=cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Garment center and height
center_z = 0.35
target_dist = 2.15

views = [
    ("front", (0.0, -target_dist, center_z), (math.radians(90), 0, 0)),
    ("persp", (target_dist * 0.55, -target_dist * 0.85, center_z + 0.15), (math.radians(85), 0, math.radians(32))),
    ("side", (target_dist, 0.0, center_z), (math.radians(90), 0, math.radians(90))),
    ("back", (0.0, target_dist, center_z), (math.radians(90), 0, math.radians(180))),
    ("collar_zoom", (0.35, -0.75, 0.65), (math.radians(72), 0, math.radians(25)))
]

for view_name, pos, rot in views:
    cam_obj.location = pos
    cam_obj.rotation_euler = rot
    if view_name == "collar_zoom":
        cam_data.lens = 85
    else:
        cam_data.lens = 70
        
    out_file = os.path.join(out_dir, f"{prefix}_{view_name}.png")
    scene.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED: {out_file}")

print("ALL_RENDERS_COMPLETE")
