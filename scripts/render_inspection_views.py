import sys
sys.path.insert(0, '/Users/pradeepyadav/Desktop/Codiotic/GARMENT_STUDIO')
import bpy
import math

def render_model(glb_path, out_prefix):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb_path)
    
    # Setup scene
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'RenderSettings') and 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    
    # Camera
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    # Light
    light_data = bpy.data.lights.new("Sun", type='SUN')
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new("Sun", light_data)
    light_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))
    scene.collection.objects.link(light_obj)
    
    # Second light for fill
    fill_data = bpy.data.lights.new("Fill", type='SUN')
    fill_data.energy = 1.5
    fill_obj = bpy.data.objects.new("Fill", fill_data)
    fill_obj.rotation_euler = (math.radians(-30), math.radians(-20), math.radians(210))
    scene.collection.objects.link(fill_obj)
    
    # Material: ensure visible solid/clay or default
    obj = [o for o in scene.objects if o.type == 'MESH'][0]
    
    # Bounding box center
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_x = min(v.x for v in bbox)
    max_x = max(v.x for v in bbox)
    min_y = min(v.y for v in bbox)
    max_y = max(v.y for v in bbox)
    min_z = min(v.z for v in bbox)
    max_z = max(v.z for v in bbox)
    center = Vector(((min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2))
    
    # 1. Front View
    cam_obj.location = (center.x, center.y - 1.5, center.z)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    scene.render.filepath = f"/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images/{out_prefix}_front.png"
    bpy.ops.render.render(write_still=True)
    
    # 2. Shoulder Close-up View (Right Shoulder)
    cam_obj.location = (center.x + 0.22, center.y - 0.55, max_z - 0.05)
    cam_obj.rotation_euler = (math.radians(80), math.radians(10), math.radians(-15))
    scene.render.filepath = f"/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images/{out_prefix}_shoulder_closeup.png"
    bpy.ops.render.render(write_still=True)
    
    # 3. Top View
    cam_obj.location = (center.x, center.y, center.z + 1.6)
    cam_obj.rotation_euler = (0, 0, 0)
    scene.render.filepath = f"/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images/{out_prefix}_top.png"
    bpy.ops.render.render(write_still=True)
    
    # 4. Perspective Angled View
    cam_obj.location = (center.x + 0.9, center.y - 1.2, center.z + 0.6)
    cam_obj.rotation_euler = (math.radians(65), math.radians(0), math.radians(35))
    scene.render.filepath = f"/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images/{out_prefix}_persp.png"
    bpy.ops.render.render(write_still=True)
    
    print(f"Rendered {out_prefix} views successfully!")

from mathutils import Vector
render_model("/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/.user_uploaded/media_1794982315074_31e736df.glb", "uploaded_glb")
render_model("/tmp/test_garment.glb", "current_code")
