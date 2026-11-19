import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector

def run():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()

    # Create a simple quad or cylinder to verify UV and texture embedding
    uv_layer = bm.loops.layers.uv.new("UVMap")

    v1 = bm.verts.new((-0.2, 0.0, 0.0))
    v2 = bm.verts.new(( 0.2, 0.0, 0.0))
    v3 = bm.verts.new(( 0.2, 0.0, 0.6))
    v4 = bm.verts.new((-0.2, 0.0, 0.6))

    face = bm.faces.new([v1, v2, v3, v4])
    # Assign UVs: (0.1, 0.1), (0.45, 0.1), (0.45, 0.85), (0.1, 0.85)
    uvs = [Vector((0.1, 0.1)), Vector((0.45, 0.1)), Vector((0.45, 0.85)), Vector((0.1, 0.85))]
    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv

    mesh = bpy.data.meshes.new("TestMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("TestObj", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Material
    mat = bpy.data.materials.new("TestMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new('ShaderNodeOutputMaterial')
    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_tex = nodes.new('ShaderNodeTexImage')

    tex_path = os.path.abspath("storage/test_texture.png")
    node_tex.image = bpy.data.images.load(tex_path)

    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    obj.data.materials.append(mat)

    out_glb = "storage/test_textured.glb"
    bpy.ops.export_scene.gltf(
        filepath=out_glb,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_image_format='AUTO'
    )
    print(f"Exported to {out_glb}. Size: {os.path.getsize(out_glb)} bytes")

if __name__ == '__main__':
    run()
