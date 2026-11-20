"""
Multi-View Master Garment Snapshot Renderer.
Renders high-resolution images for:
- Top view (Pacdora-matched elevated 52-degree perspective hero view looking into collar & chest)
- Front view
- Back view
- Side view
- Wireframe view
- Close-up of neckline
- Close-up of sleeves
- Close-up of polo collar and placket
"""
import bpy
import bmesh
import math
import sys
import os
from mathutils import Vector

argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = []

blend_path = args[0]
out_dir = args[1]
prefix = args[2]

os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.render.resolution_x = 1000
scene.render.resolution_y = 800

world = bpy.data.worlds.new("World")
scene.world = world

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
main_obj = mesh_objs[0]

# Ensure smooth shading on all polygons
for p in main_obj.data.polygons:
    p.use_smooth = True
main_obj.data.update()

# Setup camera
for c in [o for o in scene.collection.objects if o.type == 'CAMERA']:
    bpy.data.objects.remove(c, do_unlink=True)

cam_data = bpy.data.cameras.new("RenderCam")
cam_obj = bpy.data.objects.new("RenderCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

views = [
    # view_name, cam_pos, target_pos, focal_lens, is_wire
    # 1. Pacdora signature top-front hero angle (elevation 52° above horizontal)
    ("top", Vector((0.0, 0.88, 1.40)), Vector((0.0, 0.02, 0.45)), 45, False),
    ("pacdora_top", Vector((0.0, 0.88, 1.40)), Vector((0.0, 0.02, 0.45)), 45, False),
    # 2. Orthogonal standard views
    ("front", Vector((0.0, 1.95, 0.38)), Vector((0.0, 0.0, 0.38)), 62, False),
    ("back", Vector((0.0, -1.95, 0.38)), Vector((0.0, 0.0, 0.38)), 62, False),
    ("side", Vector((1.95, 0.0, 0.38)), Vector((0.0, 0.0, 0.38)), 62, False),
    ("wireframe", Vector((0.0, 1.95, 0.38)), Vector((0.0, 0.0, 0.38)), 62, True),
    # 3. Macro detail zooms
    ("neckline_zoom", Vector((0.0, 0.65, 0.82)), Vector((0.0, 0.02, 0.64)), 82, False),
    ("sleeve_zoom", Vector((-0.38, 0.72, 0.54)), Vector((-0.28, 0.02, 0.50)), 82, False),
    ("collar_placket_zoom", Vector((0.0, 0.62, 0.76)), Vector((0.0, 0.02, 0.58)), 82, False)
]

for view_name, cam_pos, target_pos, focal, is_wire in views:
    cam_obj.location = cam_pos
    direction = target_pos - cam_pos
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    cam_data.lens = focal

    wire_mod = None
    if is_wire:
        scene.display.shading.light = 'FLAT'
        wire_mod = main_obj.modifiers.new("RenderWire", type='WIREFRAME')
        wire_mod.thickness = 0.0015
    else:
        scene.display.shading.light = 'STUDIO'

    out_file = os.path.join(out_dir, f"{prefix}_{view_name}.png")
    scene.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED: {out_file}")

    if wire_mod:
        main_obj.modifiers.remove(wire_mod)

print(f"ALL_VIEWS_RENDERED for {prefix}")
