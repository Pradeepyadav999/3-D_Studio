"""Parametric 3D T-shirt Generator with Anatomical Proportions and Symmetrical Sleeves."""
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import math
import json
import numpy as np
import bpy
import bmesh
from mathutils import Vector

def solve_ellipse_radii(circ: float, aspect: float = 1.40):
    """Computes semi-major axis (a, lateral width) and semi-minor axis (b, sagittal depth)."""
    r = aspect
    denom = math.pi * (3.0 * (r + 1.0) - math.sqrt((3.0 * r + 1.0) * (r + 3.0)))
    b = circ / denom
    a = r * b

    for _ in range(5):
        curr_c = math.pi * (3.0 * (a + b) - math.sqrt((3.0 * a + b) * (a + 3.0 * b)))
        error = curr_c - circ
        if abs(error) < 1e-6:
            break
        delta = 1e-5
        b_plus = b + delta
        a_plus = r * b_plus
        c_plus = math.pi * (3.0 * (a_plus + b_plus) - math.sqrt((3.0 * a_plus + b_plus) * (a_plus + 3.0 * b_plus)))
        dc_db = (c_plus - curr_c) / delta
        b = b - error / dc_db
        a = r * b
    return a, b

def generate_perfect_tshirt(size_name="M", output_glb="storage/test_perfect_realistic.glb", texture_path=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Standard real-world T-shirt proportions for regular fit (in meters)
    # Size specs tailored for natural clothing proportions
    size_table = {
        "S":   {"chest": 1.00, "shoulder": 0.46, "length": 0.68, "sleeve": 0.20},
        "M":   {"chest": 1.06, "shoulder": 0.49, "length": 0.71, "sleeve": 0.21},
        "L":   {"chest": 1.12, "shoulder": 0.52, "length": 0.73, "sleeve": 0.22},
        "XL":  {"chest": 1.18, "shoulder": 0.55, "length": 0.75, "sleeve": 0.23},
        "XXL": {"chest": 1.24, "shoulder": 0.58, "length": 0.77, "sleeve": 0.24},
    }
    spec = size_table.get(size_name.upper(), size_table["M"])

    chest = spec["chest"]
    shoulder = spec["shoulder"]
    length = spec["length"]
    sleeve = spec["sleeve"]

    # Torso proportions
    aspect = 1.42  # Realistic chest width-to-depth ratio (52cm wide, 36cm deep)
    waist = chest * 0.96
    hem = chest * 0.98
    sleeve_opening = chest * 0.35

    a_hem, b_hem = solve_ellipse_radii(hem, aspect * 0.96)
    a_waist, b_waist = solve_ellipse_radii(waist, aspect)
    a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.02)

    # Vertical landmarks
    z_hem = 0.0
    z_waist = length * 0.38
    armhole_depth = 0.225  # 22.5 cm armhole drop
    z_underarm = length - armhole_depth

    # Shoulder and Neck landmarks
    shoulder_half_w = shoulder / 2.0  # 24.5 cm for M
    neck_half_w = 0.100              # 10.0 cm half width -> 20 cm total neck width
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(16.5)) # ~4.3 cm drop
    z_hps = length
    z_shoulder_tip = z_hps - slope_drop

    # Round crew neckline drops
    neck_front_drop = 0.092  # 9.2 cm front scoop drop
    neck_back_drop = 0.024   # 2.4 cm back scoop drop
    neck_front_depth_y = 0.082
    neck_back_depth_y = 0.068

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    N_PERIM = 32
    N_LOWER = 12
    N_UPPER = 8

    torso_rings = []

    # 1. LOWER TORSO: Multi-ring tube from hem to underarm
    for r in range(N_LOWER + 1):
        t = r / float(N_LOWER)
        if t < 0.40:
            s = t / 0.40
            s_ease = 0.5 * (1.0 - math.cos(math.pi * s))
            cur_a = a_hem * (1 - s_ease) + a_waist * s_ease
            cur_b = b_hem * (1 - s_ease) + b_waist * s_ease
        else:
            s = (t - 0.40) / 0.60
            s_ease = 0.5 * (1.0 - math.cos(math.pi * s))
            cur_a = a_waist * (1 - s_ease) + a_chest * s_ease
            cur_b = b_waist * (1 - s_ease) + b_chest * s_ease

        z_nominal = z_hem + t * z_underarm
        hem_arc_drop = 0.012 * ((1.0 - t) ** 1.8)

        ring = []
        for i in range(N_PERIM):
            theta = 2.0 * math.pi * i / N_PERIM
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)

            if sin_th > 0:
                # Front curvature with natural pectoral fullness
                y_contour = cur_b * sin_th * (1.0 + 0.05 * sin_th - 0.012 * math.sin(3.0 * theta)) + 0.008 * sin_th
                vz = z_nominal - hem_arc_drop * (sin_th ** 2)
            else:
                # Back curvature
                y_contour = cur_b * sin_th * (1.0 - 0.02 * abs(sin_th))
                vz = z_nominal - hem_arc_drop * 0.7 * (sin_th ** 2)

            x_contour = cur_a * cos_th
            v = bm.verts.new((x_contour, y_contour, vz))
            ring.append(v)
        torso_rings.append(ring)

    # Stitch lower torso
    for r in range(N_LOWER):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]
        for i in range(N_PERIM):
            i_next = (i + 1) % N_PERIM
            face = bm.faces.new([r1[i], r1[i_next], r2[i_next], r2[i]])
            is_front = (0 <= i < 16)
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
                if is_front:
                    u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38
                else:
                    u_coord = 0.735 + (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

    # 2. UPPER TORSO TOP BOUNDARY TARGETS
    top_target_coords = [None] * N_PERIM

    # FRONT PANEL TOP (col 2 to 14):
    for i in range(2, 15):
        if i <= 5:
            # Right shoulder seam front: i from 2 to 5 (3 quads)
            u_sh = (5 - i) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            y = 0.012 + 0.018 * u_sh
            z = z_hps - slope_drop * u_sh
        elif i >= 11:
            # Left shoulder seam front: i from 11 to 14 (3 quads)
            u_sh = (i - 11) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            y = 0.012 + 0.018 * u_sh
            z = z_hps - slope_drop * u_sh
        else:
            # Front round crew-neck scoop: i from 5 to 11 (6 segments across the scoop)
            k = i - 5
            phi = k / 6.0 * math.pi
            x = neck_half_w * math.cos(phi)
            y = 0.012 + (neck_front_depth_y - 0.012) * (math.sin(phi) ** 0.82)
            z = z_hps - neck_front_drop * (math.sin(phi) ** 0.82)
        top_target_coords[i] = (x, y, z)

    # BACK PANEL TOP (col 18 to 30):
    for i in range(18, 31):
        if i <= 21:
            # Left shoulder seam back: i from 18 to 21
            u_sh = (21 - i) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            y = -(0.012 + 0.018 * u_sh)
            z = z_hps - slope_drop * u_sh
        elif i >= 27:
            # Right shoulder seam back: i from 27 to 30
            u_sh = (i - 27) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            y = -(0.012 + 0.018 * u_sh)
            z = z_hps - slope_drop * u_sh
        else:
            # Back round crew-neck scoop: i from 21 to 27
            k = i - 21
            phi = k / 6.0 * math.pi
            x = -neck_half_w * math.cos(phi)
            y = -(0.012 + (neck_back_depth_y - 0.012) * (math.sin(phi) ** 0.82))
            z = z_hps - neck_back_drop * (math.sin(phi) ** 0.82)
        top_target_coords[i] = (x, y, z)

    underarm_ring = torso_rings[N_LOWER]

    for r_up in range(1, N_UPPER + 1):
        t_up = r_up / float(N_UPPER)
        t_ease = t_up * t_up * (3.0 - 2.0 * t_up)

        ring = []
        for i in range(N_PERIM):
            if top_target_coords[i] is not None:
                v_under = underarm_ring[i]
                tx, ty, tz = top_target_coords[i]

                # Scye armhole indent
                scye_in = 0.014 * math.sin(math.pi * t_up)
                if abs(tx) > neck_half_w:
                    side_sign = 1.0 if tx > 0 else -1.0
                    x_interp = v_under.co.x * (1 - t_ease) + tx * t_ease - side_sign * scye_in
                else:
                    x_interp = v_under.co.x * (1 - t_ease) + tx * t_ease

                y_interp = v_under.co.y * (1 - t_ease) + ty * t_ease
                z_interp = v_under.co.z * (1 - t_ease) + tz * t_ease
                v = bm.verts.new((x_interp, y_interp, z_interp))
            else:
                v = bm.verts.new((0, 0, z_underarm))
            ring.append(v)
        torso_rings.append(ring)

    # Stitch upper torso
    for r in range(N_LOWER, N_LOWER + N_UPPER):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]

        for i in range(2, 14):
            face = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
                u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

        for i in range(18, 30):
            face = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
                u_coord = 0.735 + (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

    # Shoulder seams
    top_ring = torso_rings[-1]
    for k in range(3):
        f1 = top_ring[2 + k]
        f2 = top_ring[3 + k]
        b1 = top_ring[30 - k]
        b2 = top_ring[29 - k]
        face = bm.faces.new([f1, f2, b2, b1])
        for loop in face.loops:
            vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
            v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
            u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38 if vy >= 0 else 0.735 + (vx / (2.2 * a_chest)) * 0.38
            loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

    for k in range(3):
        f1 = top_ring[11 + k]
        f2 = top_ring[12 + k]
        b1 = top_ring[21 - k]
        b2 = top_ring[20 - k]
        face = bm.faces.new([f1, f2, b2, b1])
        for loop in face.loops:
            vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
            v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
            u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38 if vy >= 0 else 0.735 + (vx / (2.2 * a_chest)) * 0.38
            loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

    # 3. ROUND NECKLINE & RIBBED COLLAR BAND
    neck_boundary = [top_ring[i] for i in range(5, 12)] + [top_ring[i] for i in range(21, 28)]
    N_neck = len(neck_boundary)

    collar_height = 0.022  # 2.2 cm collar height
    collar_inward = 0.015  # 1.5 cm inward
    neck_center_y = 0.007

    coll_rings = [neck_boundary]
    mid_ring = []
    for vn in neck_boundary:
        dy = vn.co.y - neck_center_y
        r_rel = math.hypot(vn.co.x, dy)
        ux = vn.co.x / r_rel if r_rel > 1e-4 else 0.0
        uy = dy / r_rel if r_rel > 1e-4 else 0.0
        mid_ring.append(bm.verts.new((vn.co.x - ux * (collar_inward * 0.55), vn.co.y - uy * (collar_inward * 0.55), vn.co.z + collar_height * 0.55)))
    coll_rings.append(mid_ring)

    top_rim = []
    for vn in neck_boundary:
        dy = vn.co.y - neck_center_y
        r_rel = math.hypot(vn.co.x, dy)
        ux = vn.co.x / r_rel if r_rel > 1e-4 else 0.0
        uy = dy / r_rel if r_rel > 1e-4 else 0.0
        top_rim.append(bm.verts.new((vn.co.x - ux * collar_inward, vn.co.y - uy * collar_inward, vn.co.z + collar_height)))
    coll_rings.append(top_rim)

    for cr in range(len(coll_rings) - 1):
        c1 = coll_rings[cr]
        c2 = coll_rings[cr + 1]
        for i in range(N_neck):
            i_next = (i + 1) % N_neck
            face = bm.faces.new([c1[i], c1[i_next], c2[i_next], c2[i]])
            u0 = 0.05 + 0.90 * (i / float(N_neck))
            u1 = 0.05 + 0.90 * ((i + 1) / float(N_neck))
            v0 = 0.93 + 0.03 * (cr / 2.0)
            v1 = 0.93 + 0.03 * ((cr + 1) / 2.0)
            uvs = [Vector((u0, v0)), Vector((u1, v0)), Vector((u1, v1)), Vector((u0, v1))]
            for loop, uv in zip(face.loops, uvs):
                loop[uv_layer].uv = uv

    # 4. SYMMETRICAL NON-TWISTED SLEEVE GENERATION
    # Collect armhole loops with identical topological order from shoulder tip down front to underarm, then up back to shoulder tip
    # Right armhole (x > 0)
    right_ah = []
    for r in range(N_LOWER + N_UPPER, N_LOWER - 1, -1):
        right_ah.append(torso_rings[r][2])
    right_ah.append(torso_rings[N_LOWER][1])
    right_ah.append(torso_rings[N_LOWER][0])
    right_ah.append(torso_rings[N_LOWER][31])
    for r in range(N_LOWER, N_LOWER + N_UPPER + 1):
        right_ah.append(torso_rings[r][30])

    # Left armhole (x < 0) - WOUND IN IDENTICAL ANATOMICAL ORDER:
    # Starts at left shoulder tip (col 14), goes down front scye to underarm (col 16), then up back scye (col 18) to shoulder tip
    left_ah = []
    for r in range(N_LOWER + N_UPPER, N_LOWER - 1, -1):
        left_ah.append(torso_rings[r][14])
    left_ah.append(torso_rings[N_LOWER][15])
    left_ah.append(torso_rings[N_LOWER][16])
    left_ah.append(torso_rings[N_LOWER][17])
    for r in range(N_LOWER, N_LOWER + N_UPPER + 1):
        left_ah.append(torso_rings[r][18])

    sleeve_rings_count = 12
    # Natural relaxed sleeve hang angle: 32 degrees below horizontal (NOT 50 degrees steep!)
    drape_deg = 32.0
    drape_rad = math.radians(drape_deg)
    fwd_deg = 2.5
    fwd_rad = math.radians(fwd_deg)

    a_cuff, b_cuff = solve_ellipse_radii(sleeve_opening, 1.15)

    def loft_perfect_sleeve(ah_loop, side_sign, u_offset):
        N_pts = len(ah_loop)
        C_ah = np.mean([np.array([v.co.x, v.co.y, v.co.z]) for v in ah_loop], axis=0)

        # Sleeve unit axis vector pointing outward, slightly forward, and downward
        w_dir = np.array([
            math.cos(drape_rad) * side_sign,
            math.sin(fwd_rad),
            -math.sin(drape_rad)
        ])
        w_unit = w_dir / np.linalg.norm(w_dir)

        # Forward/Backward axis: ALWAYS points in +Y direction for both arms!
        u_y = np.array([0.0, 1.0, 0.0])

        # Transverse vertical-ish axis perpendicular to w_unit and u_y:
        u_v = np.cross(w_unit, u_y)
        u_v = u_v / np.linalg.norm(u_v)

        # Orthogonalize u_y to w_unit:
        u_y = np.cross(u_v, w_unit)
        u_y = u_y / np.linalg.norm(u_y)

        # Decompose each armhole vertex into the local (u_y, u_v) coordinate frame
        ah_coords = []
        for v in ah_loop:
            rel = np.array([v.co.x, v.co.y, v.co.z]) - C_ah
            p_y = float(np.dot(rel, u_y))
            p_v = float(np.dot(rel, u_v))
            phi = math.atan2(p_y, p_v)
            ah_coords.append((p_y, p_v, phi))

        prev_ring = ah_loop

        for r_idx in range(1, sleeve_rings_count + 1):
            t = r_idx / float(sleeve_rings_count)
            t_ease = t * t * (3.0 - 2.0 * t)

            # Gentle fabric sag
            gravity_sag = 0.008 * (t ** 1.6)

            cur_ring = []
            for i in range(N_pts):
                p_y_base, p_v_base, phi = ah_coords[i]

                # Progressive length along arm
                cap_weight = math.cos(phi) # Top of shoulder cap has full length
                ring_disp = (sleeve * t) * (1.0 + 0.05 * max(0.0, cap_weight) * (1.0 - t_ease))

                # Target elliptical cuff in the exact same phase
                q_y_target = b_cuff * math.sin(phi)
                q_v_target = a_cuff * math.cos(phi)

                # Smooth non-crossing interpolation
                c_y = p_y_base * (1.0 - t_ease) + q_y_target * t_ease
                c_v = p_v_base * (1.0 - t_ease) + q_v_target * t_ease

                V_3d = C_ah + ring_disp * w_unit + np.array([0.0, 0.0, -gravity_sag]) + c_y * u_y + c_v * u_v
                v_new = bm.verts.new(tuple(V_3d))
                cur_ring.append(v_new)

            for i in range(N_pts):
                i_next = (i + 1) % N_pts
                # Consistent outward face normals
                if side_sign > 0:
                    face = bm.faces.new([prev_ring[i], prev_ring[i_next], cur_ring[i_next], cur_ring[i]])
                else:
                    face = bm.faces.new([prev_ring[i_next], prev_ring[i], cur_ring[i], cur_ring[i_next]])

                # Sleeve UV unwrap
                u_frac0 = i / float(N_pts)
                u_frac1 = (i + 1) / float(N_pts)
                u0 = u_offset + 0.40 * u_frac0
                u1 = u_offset + 0.40 * u_frac1
                v0 = 0.01 + 0.06 * ((r_idx - 1) / float(sleeve_rings_count))
                v1 = 0.01 + 0.06 * (r_idx / float(sleeve_rings_count))

                if side_sign > 0:
                    uvs = [Vector((u0, v0)), Vector((u1, v0)), Vector((u1, v1)), Vector((u0, v1))]
                else:
                    uvs = [Vector((u1, v0)), Vector((u0, v0)), Vector((u0, v1)), Vector((u1, v1))]

                for loop, uv in zip(face.loops, uvs):
                    loop[uv_layer].uv = uv

            prev_ring = cur_ring

    loft_perfect_sleeve(right_ah, +1.0, 0.05)
    loft_perfect_sleeve(left_ah, -1.0, 0.55)

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(f"ParametricTshirt_{size_name}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(f"Garment_{size_name}", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    subsurf = obj.modifiers.new(name="SubdivisionSurface", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Material
    mat = bpy.data.materials.new(name="GarmentMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new('ShaderNodeOutputMaterial')
    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Roughness'].default_value = 0.78
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

    if texture_path and os.path.exists(texture_path):
        node_tex = nodes.new('ShaderNodeTexImage')
        node_tex.image = bpy.data.images.load(os.path.abspath(texture_path))
        links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    else:
        node_bsdf.inputs['Base Color'].default_value = (0.86, 0.86, 0.88, 1.0)

    obj.data.materials.append(mat)
    bpy.context.view_layer.update()

    dims = obj.dimensions
    print(f"Generated dimensions: Width = {dims.x*100:.1f} cm, Height = {dims.z*100:.1f} cm, Depth = {dims.y*100:.1f} cm")

    os.makedirs(os.path.dirname(os.path.abspath(output_glb)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_glb,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_normals=True
    )
    print(f"Exported to {output_glb}. Size: {os.path.getsize(output_glb)} bytes")

if __name__ == '__main__':
    generate_perfect_tshirt(
        size_name="M",
        output_glb="storage/test_perfect_realistic.glb",
        texture_path="storage/textures/test_prod_texture.png"
    )
