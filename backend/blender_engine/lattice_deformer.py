"""Parametric Lattice / Free-Form Deformation (FFD) Engine for 3D Garment Studio.
Deforms high-fidelity master base garments (Crew-Neck & Polo) to exact custom user measurements:
- Ramanujan-accurate chest circumference / flat width scaling
- Anatomical shoulder seam-to-seam span scaling
- High-Shoulder-Point (HPS) to Bottom Hem length scaling
- Uniform preservation of collar aperture and 3D buttons (prevents oval distortion)
- Flawless preservation of UV coordinates for photorealistic graphic / texture mapping
"""
import sys
import os
import math
from typing import Dict, Any, Optional

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None
    bmesh = None
    Vector = None

from backend.blender_engine.measurement_utils import (
    solve_ellipse_radii, calculate_anatomical_landmarks
)


def apply_pbr_material(
    obj,
    config: Dict[str, Any],
    default_base_color: tuple = (0.05, 0.05, 0.07, 1.0)
):
    """
    Applies PBR Principled BSDF material to the deformed garment,
    including base color hex, texture image map, normal map, and roughness.
    """
    if not obj.data.materials:
        mat = bpy.data.materials.new(name="GarmentPBRMat")
        obj.data.materials.append(mat)
    else:
        mat = obj.data.materials[0]

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        return

    # Base Color from hex
    base_hex = config.get("base_color_hex")
    if base_hex:
        clean_hex = base_hex.lstrip("#")
        if len(clean_hex) == 6:
            r = int(clean_hex[0:2], 16) / 255.0
            g = int(clean_hex[2:4], 16) / 255.0
            b = int(clean_hex[4:6], 16) / 255.0
            bsdf.inputs['Base Color'].default_value = (r ** 2.2, g ** 2.2, b ** 2.2, 1.0)
    else:
        bsdf.inputs['Base Color'].default_value = default_base_color

    bsdf.inputs['Roughness'].default_value = 0.85

    # Texture mapping
    texture_path = config.get("texture_path")
    if texture_path and os.path.exists(texture_path):
        try:
            tex_img = bpy.data.images.load(texture_path)
            tex_node = nodes.new(type='ShaderNodeTexImage')
            tex_node.image = tex_img
            links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
        except Exception as e:
            print(f"Warning: Failed to load texture map {texture_path}: {e}")

    # Normal mapping
    normal_path = config.get("normal_path")
    if normal_path and os.path.exists(normal_path):
        try:
            norm_img = bpy.data.images.load(normal_path)
            norm_img.colorspace_settings.name = 'Non-Color'
            tex_norm_node = nodes.new(type='ShaderNodeTexImage')
            tex_norm_node.image = norm_img
            norm_map_node = nodes.new(type='ShaderNodeNormalMap')
            links.new(tex_norm_node.outputs['Color'], norm_map_node.inputs['Color'])
            links.new(norm_map_node.outputs['Normal'], bsdf.inputs['Normal'])
        except Exception as e:
            print(f"Warning: Failed to load normal map {normal_path}: {e}")


def deform_base_garment(
    base_model_path: str,
    target_measurements: Dict[str, float],
    config: Dict[str, Any],
    output_glb_path: str
) -> Dict[str, Any]:
    """
    Loads a master base garment (GLB or .blend) and deforms its vertices to match
    the target measurements exactly using anatomical landmark FFD.
    """
    if bpy is None:
        raise RuntimeError("Blender bpy module is required to execute deform_base_garment.")

    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Import Master Base Model
    if base_model_path.endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=base_model_path)
    else:
        bpy.ops.import_scene.gltf(filepath=base_model_path)

    # Find the main garment mesh object
    garment_obj = None
    button_objs = []
    for o in bpy.data.objects:
        if o.type == 'MESH':
            if "button" in o.name.lower():
                button_objs.append(o)
            elif garment_obj is None or len(o.data.vertices) > len(garment_obj.data.vertices):
                garment_obj = o

    if garment_obj is None:
        raise ValueError(f"No valid mesh found in base model: {base_model_path}")

    bpy.context.view_layer.objects.active = garment_obj
    garment_obj.select_set(True)

    # 2. Extract Base Dimensions
    bpy.context.view_layer.update()
    base_dims = garment_obj.dimensions
    base_w = base_dims.x
    base_h = base_dims.z
    base_d = base_dims.y

    # Canonical base measurements (Size M)
    # Base chest circ ≈ 1.06m, Base shoulder ≈ 0.49m, Base length ≈ 0.71m
    target_chest = float(target_measurements.get("chest", 1.06))
    target_shoulder = float(target_measurements.get("shoulder", 0.49))
    target_length = float(target_measurements.get("length", 0.71))
    target_sleeve = target_measurements.get("sleeve")

    # Solve Ramanujan target radii
    aspect = 2.45
    fit = config.get("fit", "regular")
    if fit == "slim":
        aspect = 2.38
    elif fit == "relaxed":
        aspect = 2.52

    a_target, b_target = solve_ellipse_radii(target_chest, aspect)
    # Canonical base M radii
    a_base, b_base = solve_ellipse_radii(1.06, aspect)

    # Scale factors
    scale_torso_x = a_target / a_base
    scale_torso_y = b_target / b_base
    scale_shoulder_x = target_shoulder / 0.49
    scale_z = target_length / 0.71

    # Vertical landmarks of base mesh
    z_min = min(v.co.z for v in garment_obj.data.vertices)
    z_max = max(v.co.z for v in garment_obj.data.vertices)
    total_z_span = max(0.001, z_max - z_min)
    z_underarm_norm = 0.68  # underarm level relative to height

    # 3. Apply Landmark Free-Form Deformation to Garment Vertices
    for v in garment_obj.data.vertices:
        # Normalized height t from 0 (hem) to 1 (HPS / neck)
        t = (v.co.z - z_min) / total_z_span
        t_clamped = max(0.0, min(1.0, t))

        # Vertical scaling from hem
        v.co.z = z_min + (v.co.z - z_min) * scale_z

        # Lateral X and Depth Y scaling based on height zone
        if t_clamped <= z_underarm_norm:
            # Lower Torso (hem to underarm): scale uniformly by torso factors
            v.co.x *= scale_torso_x
            v.co.y *= scale_torso_y
        else:
            # Upper Torso & Shoulders: smooth ease from torso width to shoulder width
            u_upper = (t_clamped - z_underarm_norm) / (1.0 - z_underarm_norm)
            u_ease = 0.5 * (1.0 - math.cos(math.pi * u_upper))

            # Lateral scale smoothly blends from chest width to shoulder width
            eff_scale_x = scale_torso_x * (1.0 - u_ease) + scale_shoulder_x * u_ease
            # Depth Y narrows smoothly towards neck
            eff_scale_y = scale_torso_y * (1.0 - 0.20 * u_ease)

            # Neck aperture & collar protection:
            # Vertices close to center line at high Z belong to collar / neckline
            is_collar_zone = (t_clamped > 0.88) and (abs(v.co.x) < 0.08)
            if is_collar_zone:
                # Moderate scaling to prevent collar oval distortion
                avg_scale = (eff_scale_x + eff_scale_y) * 0.5
                v.co.x *= (1.0 + (avg_scale - 1.0) * 0.40)
                v.co.y *= (1.0 + (avg_scale - 1.0) * 0.40)
            else:
                v.co.x *= eff_scale_x
                v.co.y *= eff_scale_y

    garment_obj.data.update()

    # 4. Update Button Positions (if separate button objects exist)
    for b_obj in button_objs:
        b_z = b_obj.location.z
        t_b = (b_z - z_min) / total_z_span
        b_obj.location.z = z_min + (b_z - z_min) * scale_z
        b_obj.location.y *= scale_torso_y
        # Buttons retain uniform circular scaling

    bpy.context.view_layer.update()

    # 5. Apply Material & Texture
    apply_pbr_material(garment_obj, config)

    # 6. Export Binary GLB
    os.makedirs(os.path.dirname(os.path.abspath(output_glb_path)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_glb_path,
        export_format='GLB',
        use_selection=False,  # export full garment + buttons
        export_materials='EXPORT',
        export_normals=True,
        export_yup=True
    )

    final_dims = garment_obj.dimensions
    return {
        "status": "success",
        "method": "hybrid_base_mesh_lattice_scaling",
        "garment_type": config.get("garment_type", "basic_crew"),
        "vertex_count": len(garment_obj.data.vertices),
        "face_count": len(garment_obj.data.polygons),
        "dimensions": {
            "width_m": round(final_dims.x, 4),
            "height_m": round(final_dims.z, 4),
            "depth_m": round(final_dims.y, 4)
        }
    }
