"""Test script to verify Blender parametric T-shirt generation and GLB export."""
import sys
import os
import json
import math

try:
    import bpy
    import bmesh
except ImportError:
    print("Not running inside Blender Python environment")
    sys.exit(1)

def build_parametric_tshirt(params: dict, output_glb_path: str):
    # Clear existing objects in scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    chest = params.get("chest", 1.07)       # circumference in meters
    shoulder = params.get("shoulder", 0.46) # shoulder width in meters
    length = params.get("length", 0.71)     # length in meters
    sleeve = params.get("sleeve", 0.20)     # sleeve length in meters
    waist = params.get("waist", chest * 0.96)
    hem = params.get("hem", chest * 0.98)
    sleeve_opening = params.get("sleeve_opening", chest * 0.35)

    # 1. Compute radii using Ramanujan's formula
    def solve_radii(circ, aspect=1.45):
        denom = math.pi * (3.0 * (aspect + 1.0) - math.sqrt((3.0 * aspect + 1.0) * (aspect + 3.0)))
        b = circ / denom
        a = aspect * b
        return a, b

    a_hem, b_hem = solve_radii(hem, 1.40)
    a_waist, b_waist = solve_radii(waist, 1.42)
    a_chest, b_chest = solve_radii(chest, 1.48)

    # Key vertical heights
    z_hem = 0.0
    z_waist = length * 0.45
    armhole_depth = max(0.18, shoulder * 0.46)
    z_underarm = length - armhole_depth
    z_shoulder_tip = length - 0.04
    z_shoulder_neck = length

    # Torso rings setup
    num_torso_pts = 32  # perimeter vertices per ring
    # Half-width and half-depth at shoulder
    shoulder_half_w = shoulder / 2.0
    neck_half_w = shoulder * 0.22

    bm = bmesh.new()

    # Generate lower torso rings (hem to underarm)
    num_lower_rings = 8
    torso_rings = []
    for r in range(num_lower_rings + 1):
        t = r / float(num_lower_rings)
        z = z_hem + t * z_underarm
        # Interpolate radii
        if t < 0.5:
            s = t / 0.5
            a = a_hem * (1 - s) + a_waist * s
            b = b_hem * (1 - s) + b_waist * s
        else:
            s = (t - 0.5) / 0.5
            a = a_waist * (1 - s) + a_chest * s
            b = b_waist * (1 - s) + b_chest * s

        ring_verts = []
        for i in range(num_torso_pts):
            theta = 2.0 * math.pi * i / num_torso_pts
            # theta = 0 is Right (+X), pi/2 is Front (+Y), pi is Left (-X), 3pi/2 is Back (-Y)
            y_scale = 1.05 if math.sin(theta) > 0 else 0.95
            vx = a * math.cos(theta)
            vy = b * math.sin(theta) * y_scale
            vert = bm.verts.new((vx, vy, z))
            ring_verts.append(vert)
        torso_rings.append(ring_verts)

    # Stitch lower torso rings together
    for r in range(num_lower_rings):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]
        for i in range(num_torso_pts):
            i_next = (i + 1) % num_torso_pts
            bm.faces.new([r1[i], r1[i_next], r2[i_next], r2[i]])

    # Build Upper Torso: Front & Back panels + Neckline & Shoulders
    # Indices around underarm ring (num_torso_pts = 32):
    # Right lateral side: i = 0 (x > 0)
    # Front center: i = 8 (y > 0)
    # Left lateral side: i = 16 (x < 0)
    # Back center: i = 24 (y < 0)
    # Right armhole opening: i in [28..31, 0..4]
    # Front chest panel: i in [4..12]
    # Left armhole opening: i in [12..20]
    # Back chest panel: i in [20..28]

    # Generate shoulder & collar top vertices
    # High shoulder point left & right
    v_neck_rf = bm.verts.new((neck_half_w, b_chest * 0.35, z_shoulder_neck - 0.08)) # right front neck
    v_neck_lf = bm.verts.new((-neck_half_w, b_chest * 0.35, z_shoulder_neck - 0.08)) # left front neck
    v_neck_rb = bm.verts.new((neck_half_w, -b_chest * 0.30, z_shoulder_neck - 0.025)) # right back neck
    v_neck_lb = bm.verts.new((-neck_half_w, -b_chest * 0.30, z_shoulder_neck - 0.025)) # left back neck

    v_neck_f_center = bm.verts.new((0.0, b_chest * 0.55, z_shoulder_neck - 0.11)) # front collar drop
    v_neck_b_center = bm.verts.new((0.0, -b_chest * 0.40, z_shoulder_neck - 0.035)) # back collar drop

    # Shoulder tips
    v_sh_right_f = bm.verts.new((shoulder_half_w, b_chest * 0.20, z_shoulder_tip))
    v_sh_right_b = bm.verts.new((shoulder_half_w, -b_chest * 0.20, z_shoulder_tip))
    v_sh_left_f = bm.verts.new((-shoulder_half_w, b_chest * 0.20, z_shoulder_tip))
    v_sh_left_b = bm.verts.new((-shoulder_half_w, -b_chest * 0.20, z_shoulder_tip))

    top_ring = torso_rings[-1]

    # Stitch front torso to neckline
    # Front vertices on top ring: indices 5, 6, 7, 8, 9, 10, 11
    bm.faces.new([top_ring[5], top_ring[6], top_ring[7], v_sh_right_f])
    bm.faces.new([top_ring[7], top_ring[8], v_neck_f_center, v_neck_rf])
    bm.faces.new([v_sh_right_f, top_ring[7], v_neck_rf])
    bm.faces.new([top_ring[8], top_ring[9], top_ring[10], v_neck_lf])
    bm.faces.new([top_ring[8], v_neck_lf, v_neck_f_center])
    bm.faces.new([top_ring[10], top_ring[11], v_sh_left_f, v_neck_lf])

    # Stitch back torso to neckline
    # Back vertices on top ring: indices 21, 22, 23, 24, 25, 26, 27
    bm.faces.new([top_ring[21], top_ring[22], top_ring[23], v_sh_left_b])
    bm.faces.new([top_ring[23], top_ring[24], v_neck_b_center, v_neck_lb])
    bm.faces.new([v_sh_left_b, top_ring[23], v_neck_lb])
    bm.faces.new([top_ring[24], top_ring[25], top_ring[26], v_neck_rb])
    bm.faces.new([top_ring[24], v_neck_rb, v_neck_b_center])
    bm.faces.new([top_ring[26], top_ring[27], v_sh_right_b, v_neck_rb])

    # Shoulder seam faces (connecting front to back over shoulder)
    bm.faces.new([v_sh_right_f, v_neck_rf, v_neck_rb, v_sh_right_b])
    bm.faces.new([v_sh_left_f, v_sh_left_b, v_neck_lb, v_neck_lf])

    # Collar rim (subtle thickness ring around neck)
    v_coll_f = bm.verts.new((0.0, b_chest * 0.52, z_shoulder_neck - 0.125))
    v_coll_rf = bm.verts.new((neck_half_w * 0.9, b_chest * 0.32, z_shoulder_neck - 0.095))
    v_coll_lf = bm.verts.new((-neck_half_w * 0.9, b_chest * 0.32, z_shoulder_neck - 0.095))
    v_coll_b = bm.verts.new((0.0, -b_chest * 0.38, z_shoulder_neck - 0.045))
    v_coll_rb = bm.verts.new((neck_half_w * 0.9, -b_chest * 0.28, z_shoulder_neck - 0.038))
    v_coll_lb = bm.verts.new((-neck_half_w * 0.9, -b_chest * 0.28, z_shoulder_neck - 0.038))

    bm.faces.new([v_neck_f_center, v_neck_rf, v_coll_rf, v_coll_f])
    bm.faces.new([v_neck_rf, v_neck_rb, v_coll_rb, v_coll_rf])
    bm.faces.new([v_neck_rb, v_neck_b_center, v_coll_b, v_coll_rb])
    bm.faces.new([v_neck_b_center, v_neck_lb, v_coll_lb, v_coll_b])
    bm.faces.new([v_neck_lb, v_neck_lf, v_coll_lf, v_coll_lb])
    bm.faces.new([v_neck_lf, v_neck_f_center, v_coll_f, v_coll_lf])

    # Left & Right Sleeves
    # Build sleeves as lofted cylinders connecting to armhole vertices
    # Armhole boundaries:
    # Right: [v_sh_right_f, top_ring[4], top_ring[3], top_ring[2], top_ring[1], top_ring[0], top_ring[31], top_ring[30], top_ring[29], top_ring[28], v_sh_right_b]
    # Left: [v_sh_left_f, top_ring[12], top_ring[13], top_ring[14], top_ring[15], top_ring[16], top_ring[17], top_ring[18], top_ring[19], top_ring[20], v_sh_left_b]
    # Build parametric sleeves
    arm_circ = sleeve_opening
    a_cuff, b_cuff = solve_radii(arm_circ, 1.15)
    sleeve_rings_count = 6

    # Function to build lofted sleeve
    def build_sleeve(side_sign):
        # side_sign = +1 for right, -1 for left
        sh_tip_x = shoulder_half_w * side_sign
        sh_tip_z = z_shoulder_tip
        cuff_center_x = (shoulder_half_w + sleeve * math.cos(math.radians(35))) * side_sign
        cuff_center_y = sleeve * 0.08  # slight forward angle
        cuff_center_z = z_shoulder_tip - sleeve * math.sin(math.radians(35))

        # Sleeve cross section points
        sleeve_pts_count = 12
        prev_ring = []

        # Connect sleeve base to armhole
        for r_idx in range(sleeve_rings_count + 1):
            t_sl = r_idx / float(sleeve_rings_count)
            cx = sh_tip_x * (1 - t_sl) + cuff_center_x * t_sl
            cy = t_sl * cuff_center_y
            cz = sh_tip_z * (1 - t_sl) + cuff_center_z * t_sl

            # radius tapers from armhole size to cuff
            cur_r = (armhole_depth * 0.55) * (1 - t_sl) + a_cuff * t_sl
            cur_rz = (armhole_depth * 0.70) * (1 - t_sl) + b_cuff * t_sl

            cur_ring = []
            for sp in range(sleeve_pts_count):
                ang = 2.0 * math.pi * sp / sleeve_pts_count
                px = cx + cur_r * math.cos(ang) * 0.3 * side_sign
                py = cy + cur_r * math.sin(ang)
                pz = cz + cur_rz * math.cos(ang)
                v = bm.verts.new((px, py, pz))
                cur_ring.append(v)

            if prev_ring:
                for sp in range(sleeve_pts_count):
                    sp_next = (sp + 1) % sleeve_pts_count
                    if side_sign > 0:
                        bm.faces.new([prev_ring[sp], prev_ring[sp_next], cur_ring[sp_next], cur_ring[sp]])
                    else:
                        bm.faces.new([prev_ring[sp_next], prev_ring[sp], cur_ring[sp], cur_ring[sp_next]])
            prev_ring = cur_ring

        # Bridge base of sleeve to upper torso armhole region
        # Bridge with top_ring vertices
        if side_sign > 0:
            bm.faces.new([v_sh_right_f, prev_ring[0], v_sh_right_b])
            bm.faces.new([top_ring[4], v_sh_right_f, prev_ring[1]])
            bm.faces.new([top_ring[28], prev_ring[11], v_sh_right_b])
        else:
            bm.faces.new([v_sh_left_f, v_sh_left_b, prev_ring[0]])
            bm.faces.new([top_ring[12], prev_ring[1], v_sh_left_f])
            bm.faces.new([top_ring[20], v_sh_left_b, prev_ring[11]])

    build_sleeve(+1.0) # Right sleeve
    build_sleeve(-1.0) # Left sleeve

    # Finalize BMesh
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new("ParametricTshirtMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("ParametricTshirt", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Apply Solidify modifier for realistic fabric thickness
    solid_mod = obj.modifiers.new(name="FabricThickness", type='SOLIDIFY')
    solid_mod.thickness = 0.0018
    solid_mod.offset = 0.0
    solid_mod.use_rim = True

    # Subdivision surface modifier for smooth garment curves
    sub_mod = obj.modifiers.new(name="SmoothSurface", type='SUBSURF')
    sub_mod.levels = 1
    sub_mod.render_levels = 1

    # Set Smooth Shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    # Neutral Matte Studio Fabric PBR Material
    mat = bpy.data.materials.new(name="GarmentStudioCotton")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        # Off-white / neutral studio garment tone
        bsdf.inputs['Base Color'].default_value = (0.88, 0.88, 0.90, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.78
    obj.data.materials.append(mat)

    # Compute bounding box and metadata
    bpy.context.view_layer.update()
    dims = obj.dimensions
    vert_count = len(mesh.vertices)
    face_count = len(mesh.polygons)

    # Export to GLB
    os.makedirs(os.path.dirname(os.path.abspath(output_glb_path)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_normals=True
    )

    metadata = {
        "vertex_count": vert_count,
        "face_count": face_count,
        "dimensions": {
            "width_m": round(dims.x, 4),
            "height_m": round(dims.z, 4),
            "depth_m": round(dims.y, 4)
        }
    }
    print("GENERATION_METADATA:" + json.dumps(metadata))
    print(f"GLB successfully exported to: {output_glb_path}")

if __name__ == "__main__":
    # Test execution
    test_params = {
        "chest": 1.07,
        "shoulder": 0.46,
        "length": 0.71,
        "sleeve": 0.20
    }
    out_path = os.path.abspath("storage/generated_models/test_tshirt.glb")
    build_parametric_tshirt(test_params, out_path)
