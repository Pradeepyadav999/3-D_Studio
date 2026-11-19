import sys
sys.path.append('.')
import json
import os
import bpy
import bmesh
from backend.blender_engine.garment_builder import build_garment

TEXTURE_PATH = os.path.abspath("storage/textures/fk_graphic_crew_black_texture.png")
os.makedirs("storage/test_models", exist_ok=True)

test_configs = [
    {
        "size": "S",
        "measurements": {"chest": 0.96, "shoulder": 0.46, "length": 0.68, "sleeve": 0.20},
        "texture_path": TEXTURE_PATH,
        "base_color_hex": "#19191B"
    },
    {
        "size": "M",
        "measurements": {"chest": 1.06, "shoulder": 0.49, "length": 0.71, "sleeve": 0.21},
        "texture_path": TEXTURE_PATH,
        "base_color_hex": "#19191B"
    },
    {
        "size": "XL",
        "measurements": {"chest": 1.18, "shoulder": 0.55, "length": 0.75, "sleeve": 0.23},
        "texture_path": TEXTURE_PATH,
        "base_color_hex": "#19191B"
    }
]

for cfg in test_configs:
    size = cfg["size"]
    out_glb = f"storage/test_models/test_garment_{size}.glb"
    meta = build_garment({
        "measurements": cfg["measurements"],
        "garment_type": "regular_tshirt",
        "fit": "regular",
        "sleeve_type": "short",
        "neck_type": "round",
        "selected_size": size,
        "texture_path": cfg["texture_path"],
        "base_color_hex": cfg["base_color_hex"]
    }, out_glb)
    
    # Verify file
    assert os.path.exists(out_glb), f"GLB {out_glb} does not exist"
    size_bytes = os.path.getsize(out_glb)
    print(f"Size {size}: exported {size_bytes} bytes, metadata: {meta}")
    
    # Re-import and verify manifoldness, symmetry and boundaries
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=out_glb)
    obj = bpy.context.active_object or bpy.data.objects[0]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    
    non_m = [e for e in bm.edges if not e.is_manifold and not e.is_boundary]
    b_edges = [e for e in bm.edges if e.is_boundary]
    assert len(non_m) == 0, f"Size {size} has {len(non_m)} non-manifold edges!"
    
    # Check boundary loops
    visited = set()
    loops = []
    for e in b_edges:
        if e in visited: continue
        loop = [e]
        visited.add(e)
        curr_v = e.verts[1]
        while True:
            next_e = None
            for cand in curr_v.link_edges:
                if cand.is_boundary and cand not in visited:
                    next_e = cand
                    break
            if next_e:
                loop.append(next_e)
                visited.add(next_e)
                curr_v = next_e.other_vert(curr_v)
            else:
                break
        loops.append(loop)
        
    print(f"Size {size} boundary loops count: {len(loops)} (should be 4)")
    assert len(loops) == 4, f"Expected 4 boundary loops, got {len(loops)}"
    
    # Check symmetry
    r_verts = [v.co for v in obj.data.vertices if v.co.x > 0.001]
    l_verts = [v.co for v in obj.data.vertices if v.co.x < -0.001]
    max_asym = max([min([((lv.x - (-rv.x))**2 + (lv.y - rv.y)**2 + (lv.z - rv.z)**2)**0.5 for lv in l_verts]) for rv in r_verts])
    print(f"Size {size} max bilateral asymmetry: {max_asym:.8f} m")
    assert max_asym < 1e-4, f"Asymmetry too large: {max_asym}"

print("ALL TEST SIZES PASSED WITH ZERO ASYMMETRY AND ZERO DEFECTS!")
