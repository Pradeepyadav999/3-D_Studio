"""Phase 6: Full Size-Matrix Testing & Multi-Angle Verification Rendering Engine.
Generates all 8 standard sizes (XS through 4XL) for both Plain Crew-Neck and Polo T-Shirts.
Audits every generated model against strict ±0.50 cm tolerance.
Renders multi-angle verification cameras: Front, Top (Pacdora), Side, Back, and Collar Zoom using Blender Workbench.
"""
import sys
import os
import json
import math
from typing import Dict, Any, Tuple, Optional, List

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
for p in [current_dir, project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None

from backend.blender_engine.garment_deformer import generate_measurement_driven_garment
from backend.validation.garment_geometry_auditor import GarmentGeometryAuditor, TOLERANCE_CM


FULL_SIZE_MATRIX = {
    "XS":  {"chest": 0.94, "shoulder": 0.43, "length": 0.66, "sleeve": 0.19},
    "S":   {"chest": 1.00, "shoulder": 0.46, "length": 0.68, "sleeve": 0.20},
    "M":   {"chest": 1.06, "shoulder": 0.49, "length": 0.71, "sleeve": 0.21},
    "L":   {"chest": 1.12, "shoulder": 0.52, "length": 0.73, "sleeve": 0.22},
    "XL":  {"chest": 1.18, "shoulder": 0.55, "length": 0.75, "sleeve": 0.23},
    "XXL": {"chest": 1.24, "shoulder": 0.58, "length": 0.77, "sleeve": 0.24},
    "3XL": {"chest": 1.30, "shoulder": 0.61, "length": 0.79, "sleeve": 0.25},
    "4XL": {"chest": 1.36, "shoulder": 0.64, "length": 0.81, "sleeve": 0.26},
}

RENDERS_DIR = os.path.join(project_root, "verification_renders")
os.makedirs(RENDERS_DIR, exist_ok=True)
MODELS_DIR = os.path.join(project_root, "storage/generated_models")
os.makedirs(MODELS_DIR, exist_ok=True)


def setup_render_scene(scene):
    """Sets up robust, hardware-independent Workbench studio renderer."""
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'SINGLE'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 900
    scene.render.film_transparent = True
    world = bpy.data.worlds.new("World")
    scene.world = world


def orient_camera(cam_obj, cam_pos: Vector, target_pos: Vector, focal: float = 65.0):
    cam_obj.location = cam_pos
    direction = target_pos - cam_pos
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    cam_obj.data.lens = focal


def run_full_matrix_generation_and_validation() -> Dict[str, Any]:
    """Generates all 16 models, validates tolerances, and renders verification views."""
    all_results = {}
    rendered_files = []

    garment_types = [
        ("plain_crew", "Plain Crew-Neck T-Shirt", "#1d4ed8"),
        ("polo", "Polo T-Shirt", "#047857"),
    ]

    for g_key, g_title, hex_col in garment_types:
        all_results[g_key] = {}
        print(f"\n=======================================================")
        print(f" GENERATING FULL SIZE MATRIX: {g_title.upper()}")
        print(f"=======================================================")

        for sz_name, sz_vals in FULL_SIZE_MATRIX.items():
            glb_path = os.path.join(MODELS_DIR, f"phase6_{g_key}_{sz_name}.glb")
            cfg = {
                "garment_type": g_key,
                "selected_size": sz_name,
                "measurements": sz_vals,
                "base_color_hex": hex_col,
                "fabric_texture_type": "cotton_jersey" if g_key == "plain_crew" else "cotton_pique"
            }
            
            # 1. Generate & Deform
            meta = generate_measurement_driven_garment(cfg, glb_path)
            
            # 2. Audit against strict tolerance
            targets_cm = {
                "chest": sz_vals["chest"] * 100.0,
                "shoulder": sz_vals["shoulder"] * 100.0,
                "length": sz_vals["length"] * 100.0,
                "sleeve": sz_vals["sleeve"] * 100.0
            }
            audit = GarmentGeometryAuditor.audit_glb(
                glb_path, targets_cm, measured_override=meta.get("measured_mesh_cm")
            )
            all_results[g_key][sz_name] = audit

            cc = audit["chest_circumference"]
            sw = audit["shoulder_width"]
            bl = audit["body_length"]
            print(f"  [{sz_name:4s}] Chest: {cc['actual_glb_cm']:6.2f} (diff {cc['difference_cm']:.2f}) | "
                  f"Sh: {sw['actual_glb_cm']:5.2f} (diff {sw['difference_cm']:.2f}) | "
                  f"Len: {bl['actual_glb_cm']:5.2f} (diff {bl['difference_cm']:.2f}) | "
                  f"Status: {audit['overall_status']}")

        # Render key visual comparison sizes: XS, M, 4XL across multiple angles
        for render_sz in ["XS", "M", "4XL"]:
            glb_to_render = os.path.join(MODELS_DIR, f"phase6_{g_key}_{render_sz}.glb")
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=glb_to_render)
            
            mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
            main_obj = mesh_objs[0]

            dims = main_obj.dimensions
            center_z = dims.z * 0.50
            target_pt = Vector((0.0, 0.0, center_z))
            scene = bpy.context.scene
            setup_render_scene(scene)

            # Camera creation
            cam_data = bpy.data.cameras.new("RenderCam")
            cam_obj = bpy.data.objects.new("RenderCam", cam_data)
            scene.collection.objects.link(cam_obj)
            scene.camera = cam_obj

            dist_mult = max(dims.x, dims.z) * 2.35

            # Camera Angle Presets (Front panel is at +Y)
            views = [
                # Front View
                (f"phase6_{g_key}_{render_sz}_front.png", Vector((0.0, dist_mult, center_z)), target_pt, 52.0, False),
                # Top / Pacdora Elevated Hero View (52° elevation)
                (f"phase6_{g_key}_{render_sz}_top.png", Vector((0.0, dist_mult * 0.55, center_z + dist_mult * 0.90)), Vector((0.0, 0.0, center_z + dims.z * 0.15)), 46.0, False),
                # Side Profile View
                (f"phase6_{g_key}_{render_sz}_side.png", Vector((dist_mult, 0.0, center_z)), target_pt, 52.0, False),
                # Back View
                (f"phase6_{g_key}_{render_sz}_back.png", Vector((0.0, -dist_mult, center_z)), target_pt, 52.0, False),
                # Collar Detail Zoom
                (f"phase6_{g_key}_{render_sz}_collar_zoom.png", Vector((0.0, 0.70, dims.z - 0.02)), Vector((0.0, 0.0, dims.z - 0.06)), 80.0, False),
            ]

            for fn, c_pos, t_pos, f_lens, is_wire in views:
                orient_camera(cam_obj, c_pos, t_pos, f_lens)
                out_png = os.path.join(RENDERS_DIR, fn)
                scene.render.filepath = out_png
                bpy.ops.render.render(write_still=True)
                rendered_files.append(out_png)
                print(f"    Rendered: {fn}")

    summary_file = os.path.join(RENDERS_DIR, "phase6_audit_summary.json")
    with open(summary_file, "w") as f:
        json.dump(all_results, f, indent=2)

    return {
        "results": all_results,
        "rendered_files": rendered_files,
        "summary_file": summary_file
    }


def main():
    res = run_full_matrix_generation_and_validation()
    print("PHASE6_SUMMARY_SAVED:" + res["summary_file"])


if __name__ == "__main__" and bpy is not None:
    main()
