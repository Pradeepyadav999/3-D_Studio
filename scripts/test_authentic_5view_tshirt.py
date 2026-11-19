"""Authentic Parametric 3D T-shirt Generator with True Cross-Section Anatomy.
Eliminates all triangular chest collapse, produces a genuine round crew neck,
natural anatomical shoulders, and symmetrical draped sleeves.
"""
import os
import sys
import math
import numpy as np

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None
    bmesh = None
    Vector = None


def solve_ellipse_radii(circ: float, aspect: float = 1.42):
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


def build_authentic_garment(measurements: dict, output_glb_path: str, texture_path: str = None) -> dict:
    if bpy is None:
        raise RuntimeError("Blender bpy is required.")

    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Primary dimensions strictly from size card (in meters)
    chest = float(measurements.get("chest", 1.06))
    shoulder = float(measurements.get("shoulder", 0.49))
    length = float(measurements.get("length", 0.71))
    sleeve = float(measurements.get("sleeve", 0.21))

    # Proportions
    aspect = 1.42
    waist = float(measurements.get("waist") or (chest * 0.96))
    hem = float(measurements.get("hem") or (chest * 0.98))
    sleeve_opening = float(measurements.get("sleeve_opening") or (chest * 0.35))

    a_hem, b_hem = solve_ellipse_radii(hem, aspect * 0.96)
    a_waist, b_waist = solve_ellipse_radii(waist, aspect)
    a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.02)

    # Vertical landmarks
    z_hem = 0.0
    z_waist = length * 0.38
    armhole_depth = float(measurements.get("armhole_depth") or max(0.19, shoulder * 0.45))
    z_underarm = length - armhole_depth

    shoulder_half_w = shoulder / 2.0
    neck_half_w = float(measurements.get("neck_width", 0)) / 2.0 if measurements.get("neck_width") else shoulder_half_w * 0.40

    z_hps = length
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(16.0))
    z_shoulder_tip = z_hps - slope_drop

    neck_front_drop = float(measurements.get("neck_drop") or 0.088)
    neck_back_drop = 0.024
    z_neck_front_base = z_hps - neck_front_drop
    z_neck_back_base = z_hps - neck_back_drop

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # GRID TOPOLOGY RESOLUTION
    # We use a structured cross-section topology:
    # 32 columns around the torso perimeter (16 front, 16 back)
    N_COLS = 32
    N_FRONT = 16
    N_BACK = 16

    # A. LOWER TORSO: Hem to Underarm (Horizontal closed rings)
    N_RINGS_LOWER = 12
    torso_rings = []

    for r in range(N_RINGS_LOWER + 1):
        t = r / float(N_RINGS_LOWER)
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
        for i in range(N_COLS):
            theta = 2.0 * math.pi * i / N_COLS
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)

            if sin_th > 0:
                # Front convex curve
                y = cur_b * sin_th * (1.0 + 0.04 * sin_th - 0.01 * math.sin(3.0 * theta)) + 0.006 * sin_th
                vz = z_nominal - hem_arc_drop * (sin_th ** 2)
            else:
                # Back gentle curve
                y = cur_b * sin_th * (1.0 - 0.02 * abs(sin_th))
                vz = z_nominal - hem_arc_drop * 0.7 * (sin_th ** 2)

            x = cur_a * cos_th
            v = bm.verts.new((x, y, vz))
            ring.append(v)
        torso_rings.append(ring)

    # Stitch lower torso
    for r in range(N_RINGS_LOWER):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]
        for i in range(N_COLS):
            i_next = (i + 1) % N_COLS
            face = bm.faces.new([r1[i], r1[i_next], r2[i_next], r2[i]])
            is_front = (0 <= i < 16)
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
                u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38 if is_front else 0.735 + (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

    # B. MID-CHEST REGION (Between Underarm and Neck Drop Base)
    # Here the chest stays BROAD and FULL (Pectoral plateau). It does NOT collapse into a triangle!
    N_RINGS_MID = 4
    for r in range(1, N_RINGS_MID + 1):
        t_mid = r / float(N_RINGS_MID)
        z_nominal = z_underarm + t_mid * (z_neck_front_base - z_underarm)

        # Scye indent curves smoothly inward from underarm to mid-armhole
        scye_indent = 0.016 * math.sin(math.pi * (t_mid * 0.7))
        cur_a = a_chest - scye_indent
        cur_b = b_chest * (1.0 - 0.12 * t_mid)

        ring = []
        for i in range(N_COLS):
            theta = 2.0 * math.pi * i / N_COLS
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)

            if sin_th > 0:
                # Full convex chest
                y = cur_b * sin_th * (1.0 + 0.04 * sin_th) + 0.008 * sin_th
            else:
                y = cur_b * sin_th * (1.0 - 0.02 * abs(sin_th))

            x = cur_a * cos_th
            v = bm.verts.new((x, y, z_nominal))
            ring.append(v)
        torso_rings.append(ring)

    # Stitch mid-chest region (indices 2..14 for front, 18..30 for back, armhole openings at sides)
    mid_start_r = N_RINGS_LOWER
    for r in range(mid_start_r, mid_start_r + N_RINGS_MID):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]

        # Front chest panel
        for i in range(2, 14):
            face = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
                u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

        # Back panel
        for i in range(18, 30):
            face = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
                u_coord = 0.735 + (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

    # C. UPPER CHEST & SHOULDERS WITH TRUE ROUND CREW NECK SCOOP
    # From z_neck_front_base up to z_hps
    N_RINGS_TOP = 4
    top_target_coords = [None] * N_COLS

    # Front top boundary (shoulders + round neck scoop)
    for i in range(2, 15):
        if i <= 5:
            # Right shoulder seam: i from 2 to 5
            u_sh = (5 - i) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            y = 0.012 + 0.015 * u_sh
            z = z_hps - slope_drop * u_sh
        elif i >= 11:
            # Left shoulder seam: i from 11 to 14
            u_sh = (i - 11) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            y = 0.012 + 0.015 * u_sh
            z = z_hps - slope_drop * u_sh
        else:
            # Round crew-neck scoop: i from 5 to 11 (6 segments)
            k = i - 5
            phi = k / 6.0 * math.pi
            x = neck_half_w * math.cos(phi)
            # True circular round neck drop:
            y = 0.012 + 0.065 * (math.sin(phi) ** 0.90)
            z = z_hps - neck_front_drop * (math.sin(phi) ** 0.90)
        top_target_coords[i] = (x, y, z)

    # Back top boundary (shoulders + shallow back scoop)
    for i in range(18, 31):
        if i <= 21:
            u_sh = (21 - i) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            y = -(0.012 + 0.015 * u_sh)
            z = z_hps - slope_drop * u_sh
        elif i >= 27:
            u_sh = (i - 27) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            y = -(0.012 + 0.015 * u_sh)
            z = z_hps - slope_drop * u_sh
        else:
            k = i - 21
            phi = k / 6.0 * math.pi
            x = -neck_half_w * math.cos(phi)
            y = -(0.012 + 0.045 * (math.sin(phi) ** 0.90))
            z = z_hps - neck_back_drop * (math.sin(phi) ** 0.90)
        top_target_coords[i] = (x, y, z)

    mid_top_ring = torso_rings[-1]

    for r_top in range(1, N_RINGS_TOP + 1):
        t_top = r_top / float(N_RINGS_TOP)
        t_ease = t_top * t_top * (3.0 - 2.0 * t_top)

        ring = []
        for i in range(N_COLS):
            if top_target_coords[i] is not None:
                v_mid = mid_top_ring[i]
                tx, ty, tz = top_target_coords[i]

                # Outward flare from scye indent to shoulder endpoints
                if abs(tx) > neck_half_w:
                    side_sign = 1.0 if tx > 0 else -1.0
                    shoulder_blend = t_ease
                    x_interp = v_mid.co.x * (1 - shoulder_blend) + tx * shoulder_blend
                else:
                    x_interp = v_mid.co.x * (1 - t_ease) + tx * t_ease

                y_interp = v_mid.co.y * (1 - t_ease) + ty * t_ease
                z_interp = v_mid.co.z * (1 - t_ease) + tz * t_ease
                v = bm.verts.new((x_interp, y_interp, z_interp))
            else:
                v = bm.verts.new((0, 0, z_underarm))
            ring.append(v)
        torso_rings.append(ring)

    # Stitch upper chest to top
    top_start_r = mid_start_r + N_RINGS_MID
    for r in range(top_start_r, top_start_r + N_RINGS_TOP):
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

    # D. SHOULDER SEAMS
    top_ring = torso_rings[-1]
    # Right shoulder: connect front col 2..5 to back col 30..27 (3 quads)
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

    # Left shoulder: connect front col 11..14 to back col 21..18 (3 quads)
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

    # E. ROUND NECK OPENING & 3D RIBBED COLLAR BAND
    neck_boundary = [top_ring[i] for i in range(5, 12)] + [top_ring[i] for i in range(21, 28)]
    N_neck = len(neck_boundary)

    collar_height = 0.024  # 2.4 cm collar height
    collar_inward = 0.014  # 1.4 cm inward taper
    neck_center_y = 0.005

    coll_rings = [neck_boundary]
    for step in [0.5, 1.0]:
        c_ring = []
        for vn in neck_boundary:
            dy = vn.co.y - neck_center_y
            r_rel = math.hypot(vn.co.x, dy)
            ux = vn.co.x / r_rel if r_rel > 1e-4 else 0.0
            uy = dy / r_rel if r_rel > 1e-4 else 0.0
            c_ring.append(bm.verts.new((
                vn.co.x - ux * (collar_inward * step),
                vn.co.y - uy * (collar_inward * step),
                vn.co.z + collar_height * step
            )))
        coll_rings.append(c_ring)

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
            for loop, uv in zip(face.loops, [Vector((u0, v0)), Vector((u1, v0)), Vector((u1, v1)), Vector((u0, v1))]):
                loop[uv_layer].uv = uv

    # F. SYMMETRICAL NON-TWISTED SLEEVES
    TOTAL_RINGS = len(torso_rings)
    right_ah = []
    for r in range(TOTAL_RINGS - 1, N_RINGS_LOWER - 1, -1):
        right_ah.append(torso_rings[r][2])
    right_ah.append(torso_rings[N_RINGS_LOWER][1])
    right_ah.append(torso_rings[N_RINGS_LOWER][0])
    right_ah.append(torso_rings[N_RINGS_LOWER][31])
    for r in range(N_RINGS_LOWER, TOTAL_RINGS):
        right_ah.append(torso_rings[r][30])

    left_ah = []
    for r in range(TOTAL_RINGS - 1, N_RINGS_LOWER - 1, -1):
        left_ah.append(torso_rings[r][14])
    left_ah.append(torso_rings[N_RINGS_LOWER][15])
    left_ah.append(torso_rings[N_RINGS_LOWER][16])
    left_ah.append(torso_rings[N_RINGS_LOWER][17])
    for r in range(N_RINGS_LOWER, TOTAL_RINGS):
        left_ah.append(torso_rings[r][18])

    sleeve_rings_count = 12
    drape_deg = 32.0
    drape_rad = math.radians(drape_deg)
    fwd_deg = 2.5
    fwd_rad = math.radians(fwd_deg)

    a_cuff, b_cuff = solve_ellipse_radii(sleeve_opening, 1.15)

    def loft_sleeve(ah_loop, side_sign, u_offset):
        N_pts = len(ah_loop)
        C_ah = np.mean([np.array([v.co.x, v.co.y, v.co.z]) for v in ah_loop], axis=0)

        w_dir = np.array([math.cos(drape_rad) * side_sign, math.sin(fwd_rad), -math.sin(drape_rad)])
        w_unit = w_dir / np.linalg.norm(w_dir)

        # Strictly upward axis
        u_v = np.array([0.0, 0.0, 1.0])
        u_v = u_v - np.dot(u_v, w_unit) * w_unit
        u_v = u_v / np.linalg.norm(u_v)

        # Strictly forward axis
        u_y = np.cross(u_v, w_unit)
        if u_y[1] < 0:
            u_y = -u_y
        u_y = u_y / np.linalg.norm(u_y)

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
            gravity_sag = 0.008 * (t ** 1.6)

            cur_ring = []
            for i in range(N_pts):
                p_y_base, p_v_base, phi = ah_coords[i]
                cap_weight = math.cos(phi)
                ring_disp = (sleeve * t) * (1.0 + 0.05 * max(0.0, cap_weight) * (1.0 - t_ease))
                q_y_target = b_cuff * math.sin(phi)
                q_v_target = a_cuff * math.cos(phi)
                c_y = p_y_base * (1.0 - t_ease) + q_y_target * t_ease
                c_v = p_v_base * (1.0 - t_ease) + q_v_target * t_ease

                V_3d = C_ah + ring_disp * w_unit + np.array([0.0, 0.0, -gravity_sag]) + c_y * u_y + c_v * u_v
                v_new = bm.verts.new(tuple(V_3d))
                cur_ring.append(v_new)

            for i in range(N_pts):
                i_next = (i + 1) % N_pts
                if side_sign > 0:
                    face = bm.faces.new([prev_ring[i], prev_ring[i_next], cur_ring[i_next], cur_ring[i]])
                else:
                    face = bm.faces.new([prev_ring[i_next], prev_ring[i], cur_ring[i], cur_ring[i_next]])

                u_frac0 = i / float(N_pts)
                u_frac1 = (i + 1) / float(N_pts)
                u0 = u_offset + 0.40 * u_frac0
                u1 = u_offset + 0.40 * u_frac1
                v0 = 0.01 + 0.06 * ((r_idx - 1) / float(sleeve_rings_count))
                v1 = 0.01 + 0.06 * (r_idx / float(sleeve_rings_count))
                uvs = [Vector((u0, v0)), Vector((u1, v0)), Vector((u1, v1)), Vector((u0, v1))] if side_sign > 0 else [Vector((u1, v0)), Vector((u0, v0)), Vector((u0, v1)), Vector((u1, v1))]
                for loop, uv in zip(face.loops, uvs):
                    loop[uv_layer].uv = uv

            prev_ring = cur_ring

    loft_sleeve(right_ah, +1.0, 0.05)
    loft_sleeve(left_ah, -1.0, 0.55)

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new("ParametricTshirt")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Garment", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    subsurf = obj.modifiers.new(name="SubdivisionSurface", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    for poly in mesh.polygons:
        poly.use_smooth = True

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
        node_bsdf.inputs['Base Color'].default_value = (0.12, 0.12, 0.14, 1.0)

    obj.data.materials.append(mat)
    bpy.context.view_layer.update()

    dims = obj.dimensions
    os.makedirs(os.path.dirname(os.path.abspath(output_glb_path)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_normals=True
    )

    return {
        "width_m": round(dims.x, 4),
        "height_m": round(dims.z, 4),
        "depth_m": round(dims.y, 4),
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.polygons)
    }

if __name__ == "__main__" and bpy is not None:
    meas = {"chest": 1.06, "shoulder": 0.49, "length": 0.71, "sleeve": 0.21}
    meta = build_authentic_garment(meas, "storage/test_authentic_tshirt.glb")
    print("Dimensions:", meta)
