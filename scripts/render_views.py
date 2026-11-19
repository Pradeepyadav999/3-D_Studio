"""Blender script to render 5 canonical views (Front, Back, Left, Right, Perspective) of a GLB model."""
import sys
import os
import math

try:
    import bpy
except ImportError:
    print("Run via Blender")
    sys.exit(1)

def render_model_views(glb_path: str, output_prefix: str):
    # Reset scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import GLB
    bpy.ops.import_scene.gltf(filepath=glb_path)

    # Find imported mesh object
    target_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            target_obj = obj
            break

    if not target_obj:
        print("No mesh found in GLB")
        return

    # Center target object at origin (0, 0, height/2)
    bpy.context.view_layer.objects.active = target_obj
    target_obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    target_obj.location = (0, 0, target_obj.dimensions.z / 2.0)

    # Set up Camera
    cam_data = bpy.data.cameras.new("StudioCamera")
    cam_data.lens = 65 # 65mm focal length for apparel product photography
    cam_obj = bpy.data.objects.new("StudioCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Studio Lighting setup
    # Key light
    key_light_data = bpy.data.lights.new("KeyLight", type='AREA')
    key_light_data.energy = 250
    key_light_data.size = 1.2
    key_light_obj = bpy.data.objects.new("KeyLight", key_light_data)
    key_light_obj.location = (1.5, -2.0, 2.2)
    key_light_obj.rotation_euler = (math.radians(50), 0, math.radians(35))
    bpy.context.collection.objects.link(key_light_obj)

    # Fill light
    fill_light_data = bpy.data.lights.new("FillLight", type='AREA')
    fill_light_data.energy = 120
    fill_light_data.size = 1.5
    fill_light_obj = bpy.data.objects.new("FillLight", fill_light_data)
    fill_light_obj.location = (-1.8, -1.5, 1.8)
    fill_light_obj.rotation_euler = (math.radians(50), 0, math.radians(-40))
    bpy.context.collection.objects.link(fill_light_obj)

    # Rim light
    rim_light_data = bpy.data.lights.new("RimLight", type='AREA')
    rim_light_data.energy = 200
    rim_light_data.size = 1.0
    rim_light_obj = bpy.data.objects.new("RimLight", rim_light_data)
    rim_light_obj.location = (0, 2.2, 1.8)
    rim_light_obj.rotation_euler = (math.radians(-45), 0, math.radians(180))
    bpy.context.collection.objects.link(rim_light_obj)

    # Render Settings
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH' # Fast, clean, professional shading
    scene.display.shading.light = 'MATCAP'
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (0.86, 0.86, 0.88)
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = 'BOTH'
    scene.display.shading.curvature_ridge_factor = 1.2
    scene.display.shading.curvature_valley_factor = 0.8

    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.film_transparent = False

    # Target lookat: center of garment
    z_center = target_obj.dimensions.z / 2.0
    dist = 1.8

    views = {
        "perspective": (dist * 0.7, -dist * 0.75, z_center + 0.35, 75, 0, 42),
        "front": (0, -dist, z_center, 90, 0, 0),
        "back": (0, dist, z_center, 90, 0, 180),
        "left": (-dist, 0, z_center, 90, 0, -90),
        "right": (dist, 0, z_center, 90, 0, 90),
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_prefix)), exist_ok=True)

    for v_name, (cx, cy, cz, rx, ry, rz) in views.items():
        cam_obj.location = (cx, cy, cz)
        cam_obj.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
        out_path = f"{output_prefix}_{v_name}.png"
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {v_name} view to: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) > 5:
        # custom invocation
        argv = sys.argv[sys.argv.index("--") + 1:]
        glb_p = argv[0]
        pref = argv[1]
    else:
        glb_p = "storage/generated_models/test_improved_tshirt.glb"
        pref = "docs/improved_model"
    render_model_views(glb_p, pref)
