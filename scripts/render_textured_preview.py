import sys
import os
import math
import bpy

def render_textured(glb_path, out_path_front, out_path_back):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb_path)

    target_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            target_obj = obj
            break

    if not target_obj:
        print("No mesh found")
        return

    bpy.context.view_layer.objects.active = target_obj
    target_obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    target_obj.location = (0, 0, target_obj.dimensions.z / 2.0)

    # Camera
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 70
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Workbench Shading with TEXTURE display
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'TEXTURE'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800

    z_center = target_obj.dimensions.z / 2.0
    dist = 1.9

    # Look at +Y surface (Front of garment where crew neck drops): camera at +Y, rot=(90, 0, 180)
    cam_obj.location = (0, dist, z_center)
    cam_obj.rotation_euler = (math.radians(90), 0, math.radians(180))
    scene.render.filepath = out_path_front
    bpy.ops.render.render(write_still=True)
    print(f"Rendered front (+Y) to {out_path_front}")

    # Look at -Y surface (Back of garment): camera at -Y, rot=(90, 0, 0)
    cam_obj.location = (0, -dist, z_center)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    scene.render.filepath = out_path_back
    print(f"Rendered back (-Y) to {out_path_back}")
    bpy.ops.render.render(write_still=True)

if __name__ == '__main__':
    render_textured(
        "storage/test_full_textured_tshirt.glb",
        "storage/test_front_render.png",
        "storage/test_back_render.png"
    )
