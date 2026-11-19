import sys
import os
sys.path.insert(0, os.path.abspath("."))
import bpy
import bmesh
from mathutils import Vector
import math
import json

from backend.blender_engine.crew_geometry_builder import build_crew_geometry
from backend.blender_engine.polo_geometry_builder import build_polo_geometry
from backend.validation.garment_geometry_auditor import GarmentGeometryAuditor

OUTPUT_DIR = os.path.abspath("storage/test_renders")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_camera_and_lighting(obj):
    # Ensure lighting and camera exist
    for o in list(bpy.data.objects):
        if o.type in ('LIGHT', 'CAMERA'):
            bpy.data.objects.remove(o, do_unlink=True)
            
    # Key light (front-right)
    key_light_data = bpy.data.lights.new(name="KeyLight", type='AREA')
    key_light_data.energy = 320.0
    key_light_data.size = 1.6
    key_light = bpy.data.objects.new(name="KeyLight", object_data=key_light_data)
    bpy.context.collection.objects.link(key_light)
    key_light.location = (1.2, 1.8, 1.4)
    key_light.rotation_euler = (math.radians(55), 0, math.radians(145))
    
    # Fill light (front-left)
    fill_light_data = bpy.data.lights.new(name="FillLight", type='AREA')
    fill_light_data.energy = 160.0
    fill_light_data.size = 2.0
    fill_light = bpy.data.objects.new(name="FillLight", object_data=fill_light_data)
    bpy.context.collection.objects.link(fill_light)
    fill_light.location = (-1.4, 1.5, 0.8)
    fill_light.rotation_euler = (math.radians(60), 0, math.radians(215))
    
    # Rim light (back)
    rim_light_data = bpy.data.lights.new(name="RimLight", type='AREA')
    rim_light_data.energy = 220.0
    rim_light_data.size = 1.2
    rim_light = bpy.data.objects.new(name="RimLight", object_data=rim_light_data)
    bpy.context.collection.objects.link(rim_light)
    rim_light.location = (0.0, -1.8, 1.2)
    rim_light.rotation_euler = (math.radians(120), 0, 0)

    # Top light
    top_light_data = bpy.data.lights.new(name="TopLight", type='AREA')
    top_light_data.energy = 80.0
    top_light_data.size = 1.5
    top_light = bpy.data.objects.new(name="TopLight", object_data=top_light_data)
    bpy.context.collection.objects.link(top_light)
    top_light.location = (0.0, -0.2, 2.2)
    top_light.rotation_euler = (0, 0, 0)
    
    # Camera
    cam_data = bpy.data.cameras.new("RenderCam")
    cam_data.lens = 65  # 65mm portrait focal length for realistic distortion-free garment mockups
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    # Render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 32
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.render.film_transparent = True
    
    return cam_obj

def render_views(cam_obj, prefix, z_center=0.35, z_collar=0.62):
    # In Blender: Front of shirt is at +Y (facing +Y), back of shirt is at -Y
    # Camera looking at Front (+Y) must be at +Y looking toward -Y: rot = (90°, 0, 180°)
    # Camera looking at Back (-Y) must be at -Y looking toward +Y: rot = (90°, 0, 0°)
    views = [
        ("front", (0.0, 2.05, z_center), (math.radians(90), 0, math.radians(180))),
        ("persp", (1.1, 1.75, z_center + 0.12), (math.radians(82), 0, math.radians(145))),
        ("side", (1.85, 0.0, z_center), (math.radians(90), 0, math.radians(90))),
        ("back", (0.0, -2.05, z_center), (math.radians(90), 0, 0)),
        ("collar", (0.0, 0.85, z_collar + 0.22), (math.radians(65), 0, math.radians(180))),
    ]
    
    for name, loc, rot in views:
        cam_obj.location = loc
        cam_obj.rotation_euler = rot
        out_path = os.path.join(OUTPUT_DIR, f"{prefix}_{name}.png")
        bpy.context.scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered: {out_path}")

def test_build(garment_type="basic_crew"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Config matching Section 19: 40" chest (1.016m), 17" shoulder (0.4318m), 28" length (0.7112m)
    config = {
        "garment_type": garment_type,
        "selected_size": "M",
        "fit": "regular",
        "measurements": {
            "chest": 1.016,
            "shoulder": 0.4318,
            "length": 0.7112,
            "sleeve": 0.21
        },
        "button_count": 2
    }
    
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
    if garment_type == "polo":
        meta = build_polo_geometry(config, bm, uv_layer)
    else:
        meta = build_crew_geometry(config, bm, uv_layer)
        
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    mesh = bpy.data.meshes.new(f"GarmentMesh_{garment_type}")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(f"GarmentObj_{garment_type}", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    for poly in mesh.polygons:
        poly.use_smooth = True
        
    # Fabric material: clean neutral studio white/lavender similar to Pacdora
    mat = bpy.data.materials.new(name="FabricMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.92, 0.91, 0.94, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.85
    obj.data.materials.append(mat)
    
    # Button material for polo
    if garment_type == "polo":
        mat_btn = bpy.data.materials.new(name="ButtonMat")
        mat_btn.use_nodes = True
        b_bsdf = mat_btn.node_tree.nodes.get("Principled BSDF")
        if b_bsdf:
            b_bsdf.inputs['Base Color'].default_value = (0.98, 0.97, 0.95, 1.0)
            b_bsdf.inputs['Roughness'].default_value = 0.20
            b_bsdf.inputs['Metallic'].default_value = 0.05
        obj.data.materials.append(mat_btn)
        
    # Export GLB
    glb_path = os.path.join(OUTPUT_DIR, f"{garment_type}_model.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_normals=True
    )
    print(f"Exported GLB: {glb_path} ({os.path.getsize(glb_path)} bytes)")
    
    # Audit GLB
    targets_cm = {"chest": 101.6, "shoulder": 43.18, "length": 71.12, "sleeve": 21.0}
    audit = GarmentGeometryAuditor.audit_glb(glb_path, targets_cm)
    print("AUDIT RESULTS for", garment_type, ":")
    print(json.dumps(audit, indent=2))
    
    cam = setup_camera_and_lighting(obj)
    render_views(cam, garment_type, z_center=0.35, z_collar=0.62)

print("=== TESTING CREW-NECK ===")
test_build("basic_crew")

print("=== TESTING POLO ===")
test_build("polo")
print("=== COMPLETED ===")
