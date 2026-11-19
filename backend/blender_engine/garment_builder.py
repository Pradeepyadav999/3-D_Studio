"""Parametric 3D Garment Generator for Blender Headless Worker.
Master orchestrator routing between dedicated garment builders:
- Basic Plain Crew-Neck T-Shirt (crew_geometry_builder)
- Polo T-Shirt (polo_geometry_builder)

Enforces dimensional accuracy, professional mesh topology, realistic PBR materials,
and standard GLB export with audit metadata.
"""
import sys
import os
import json
import math
import argparse

# Ensure workspace root is in sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None
    bmesh = None
    Vector = None

from backend.blender_engine.crew_geometry_builder import build_crew_geometry
from backend.blender_engine.polo_geometry_builder import build_polo_geometry
from backend.blender_engine.measurement_utils import solve_ellipse_radii


def build_garment(config: dict, output_glb_path: str) -> dict:
    if bpy is None:
        raise RuntimeError("Blender bpy module is required to execute build_garment.")

    # Reset scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    measurements = config.get("measurements", {})
    garment_type = config.get("garment_type", "regular_tshirt")
    fit = config.get("fit", "regular")
    sleeve_type = config.get("sleeve_type", "short")
    neck_type = config.get("neck_type", "round")
    selected_size = config.get("selected_size", "M")

    # Routing logic: Polo vs Basic Plain Crew-Neck
    is_polo = (
        garment_type in ("polo", "polo_tshirt", "mens_polo") or
        neck_type == "polo"
    )

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    if is_polo:
        builder_meta = build_polo_geometry(config, bm, uv_layer)
    else:
        builder_meta = build_crew_geometry(config, bm, uv_layer)

    # Clean up any potential orphan vertices
    orphan_verts = [v for v in bm.verts if not v.link_edges]
    if orphan_verts:
        bmesh.ops.delete(bm, geom=orphan_verts, context='VERTS')

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh_name = f"GarmentMesh_{'polo' if is_polo else 'crew'}_{selected_size}"
    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    obj_name = f"Garment_{'Polo' if is_polo else 'Crew'}_{selected_size}"
    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Setup PBR Materials
    texture_path = config.get("texture_path")
    normal_path = config.get("normal_path")
    roughness_path = config.get("roughness_path")
    base_color_hex = config.get("base_color_hex")
    fabric_texture_type = config.get("fabric_texture_type", "cotton_pique" if is_polo else "cotton_jersey")

    mat = bpy.data.materials.new(name="GarmentMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new('ShaderNodeOutputMaterial')
    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Roughness'].default_value = 0.88 if (is_polo or fabric_texture_type == "cotton_pique") else 0.84
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

    # 1. Base Color
    if texture_path and os.path.exists(texture_path):
        node_bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        node_tex = nodes.new('ShaderNodeTexImage')
        node_tex.image = bpy.data.images.load(os.path.abspath(texture_path))
        links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    elif base_color_hex:
        c_hex = base_color_hex.lstrip("#")
        if len(c_hex) == 6:
            r = int(c_hex[0:2], 16) / 255.0
            g = int(c_hex[2:4], 16) / 255.0
            b = int(c_hex[4:6], 16) / 255.0
            node_bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
        else:
            node_bsdf.inputs['Base Color'].default_value = (0.92, 0.91, 0.94, 1.0)
    else:
        node_bsdf.inputs['Base Color'].default_value = (0.92, 0.91, 0.94, 1.0)

    # 2. Normal Map
    if normal_path and os.path.exists(normal_path):
        node_norm = nodes.new('ShaderNodeNormalMap')
        node_norm.inputs['Strength'].default_value = 0.85
        node_norm_tex = nodes.new('ShaderNodeTexImage')
        node_norm_tex.image = bpy.data.images.load(os.path.abspath(normal_path))
        node_norm_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(node_norm_tex.outputs['Color'], node_norm.inputs['Color'])
        links.new(node_norm.outputs['Normal'], node_bsdf.inputs['Normal'])

    # 3. Roughness Map
    if roughness_path and os.path.exists(roughness_path):
        node_rough_tex = nodes.new('ShaderNodeTexImage')
        node_rough_tex.image = bpy.data.images.load(os.path.abspath(roughness_path))
        node_rough_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(node_rough_tex.outputs['Color'], node_bsdf.inputs['Roughness'])

    obj.data.materials.append(mat)

    # 4. Button Material for Polo
    if is_polo:
        mat_btn = bpy.data.materials.new(name="ButtonMaterial")
        mat_btn.use_nodes = True
        btn_nodes = mat_btn.node_tree.nodes
        btn_links = mat_btn.node_tree.links
        btn_nodes.clear()
        btn_out = btn_nodes.new('ShaderNodeOutputMaterial')
        btn_bsdf = btn_nodes.new('ShaderNodeBsdfPrincipled')
        btn_links.new(btn_bsdf.outputs['BSDF'], btn_out.inputs['Surface'])
        btn_bsdf.inputs['Roughness'].default_value = 0.22
        btn_bsdf.inputs['Metallic'].default_value = 0.04

        btn_hex = config.get("button_color_hex", "#F8F8F4").lstrip("#")
        if len(btn_hex) == 6:
            br = int(btn_hex[0:2], 16) / 255.0
            bg = int(btn_hex[2:4], 16) / 255.0
            bb = int(btn_hex[4:6], 16) / 255.0
            btn_bsdf.inputs['Base Color'].default_value = (br, bg, bb, 1.0)
        else:
            btn_bsdf.inputs['Base Color'].default_value = (0.97, 0.96, 0.93, 1.0)

        obj.data.materials.append(mat_btn)

    bpy.context.view_layer.update()
    dims = obj.dimensions
    vert_count = len(mesh.vertices)
    face_count = len(mesh.polygons)

    os.makedirs(os.path.dirname(os.path.abspath(output_glb_path)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_normals=True
    )

    metadata = {
        "garment_type": "polo" if is_polo else "basic_crew",
        "selected_size": selected_size,
        "fit": fit,
        "vertex_count": vert_count,
        "face_count": face_count,
        "dimensions": {
            "width_m": round(dims.x, 4),
            "height_m": round(dims.z, 4),
            "depth_m": round(dims.y, 4)
        }
    }
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Blender Parametric Garment Generator")
    parser.add_argument("--config", type=str, help="Path to JSON configuration file")
    parser.add_argument("--json", type=str, help="JSON configuration string")
    parser.add_argument("--output", type=str, required=True, help="Path to output GLB file")

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)

    if args.config and os.path.exists(args.config):
        with open(args.config, "r") as f:
            config = json.load(f)
    elif args.json:
        config = json.loads(args.json)
    else:
        raise ValueError("Either --config or --json must be specified.")

    meta = build_garment(config, args.output)
    print("GENERATION_METADATA:" + json.dumps(meta))


if __name__ == "__main__" and bpy is not None:
    main()
