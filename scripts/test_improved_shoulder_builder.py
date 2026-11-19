import sys
sys.path.insert(0, '/Users/pradeepyadav/Desktop/Codiotic/GARMENT_STUDIO')
import bpy
import bmesh
import math
import numpy as np
from mathutils import Vector
from backend.blender_engine.garment_builder import solve_ellipse_radii

def build_improved_garment(config: dict, output_glb_path: str) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)

    measurements = config.get("measurements", {})
    garment_type = config.get("garment_type", "regular_tshirt")
    fit = config.get("fit", "regular")
    sleeve_type = config.get("sleeve_type", "short")
    neck_type = config.get("neck_type", "round")
    selected_size = config.get("selected_size", "M")

    chest = float(measurements.get("chest", 1.0668))
    shoulder = float(measurements.get("shoulder", 0.4572))
    length = float(measurements.get("length", 0.7366))
    sleeve = float(measurements.get("sleeve", 0.2286 if sleeve_type == "short" else 0.64))

    if fit == "slim":
        waist_default = chest * 0.92
        hem_default = chest * 0.95
        aspect = 2.38
    elif fit == "relaxed":
        waist_default = chest * 0.98
        hem_default = chest * 1.01
        aspect = 2.52
    else:
        waist_default = chest * 0.96
        hem_default = chest * 0.98
        aspect = 2.45

    waist = float(measurements.get("waist") or waist_default)
    hem = float(measurements.get("hem") or hem_default)
    sleeve_opening = float(measurements.get("sleeve_opening") or (chest * 0.35 if sleeve_type == "short" else chest * 0.25))

    a_hem, b_hem = solve_ellipse_radii(hem, aspect * 0.97)
    a_waist, b_waist = solve_ellipse_radii(waist, aspect)
    a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.01)

    z_hem = 0.0
    z_waist = length * 0.38
    armhole_depth = float(measurements.get("armhole_depth") or max(0.18, shoulder * 0.43))
    z_underarm = length - armhole_depth

    shoulder_half_w = shoulder / 2.0
    if measurements.get("neck_width"):
        neck_half_w = float(measurements["neck_width"]) / 2.0
    elif measurements.get("neck") and float(measurements["neck"]) > 0:
        val = float(measurements["neck"])
        if val > 0.25:
            neck_half_w = (val * 0.46) / 2.0
        else:
            neck_half_w = val / 2.0
    else:
        neck_half_w = shoulder_half_w * 0.41

    z_hps = length
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(14.5))
    z_shoulder_tip = z_hps - slope_drop

    neck_front_drop = float(measurements.get("neck_drop") or 0.082)
    neck_back_drop = 0.024
    z_neck_front_base = z_hps - neck_front_drop

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    N_COLS = 32
    N_RINGS_LOWER = 12
    N_RINGS_MID = 4
    N_RINGS_TOP = 4

    torso_rings = []

    # 1. LOWER TORSO: Hem to Underarm
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

        z = z_hem + t * (z_underarm - z_hem)
        ring = []
        for i in range(N_COLS):
            theta = 2.0 * math.pi * i / N_COLS
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)
            if sin_th > 0:
                y = cur_b * sin_th * (1.0 + 0.04 * sin_th)
            else:
                y = cur_b * sin_th * (1.0 - 0.02 * abs(sin_th))
            x = cur_a * cos_th
            v = bm.verts.new((x, y, z))
            ring.append(v)
        torso_rings.append(ring)

    for r in range(N_RINGS_LOWER):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]
        for i in range(N_COLS):
            i_next = (i + 1) % N_COLS
            face = bm.faces.new([r1[i], r1[i_next], r2[i_next], r2[i]])
            is_front = (1 <= i <= 15)
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
                u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38 if is_front else 0.735 + (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), v_coord))

    # 2. MID-CHEST REGION
    for r in range(1, N_RINGS_MID + 1):
        t_mid = r / float(N_RINGS_MID)
        z_nominal = z_underarm + t_mid * (z_neck_front_base - z_underarm)
        scye_indent = 0.010 * math.sin(math.pi * (t_mid * 0.7))
        cur_a = a_chest - scye_indent
        cur_b = b_chest * (1.0 - 0.08 * t_mid)

        ring = []
        for i in range(N_COLS):
            theta = 2.0 * math.pi * i / N_COLS
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)
            if sin_th > 0:
                y = cur_b * sin_th * (1.0 + 0.03 * sin_th) + 0.005 * sin_th
            else:
                y = cur_b * sin_th * (1.0 - 0.02 * abs(sin_th))
            x = cur_a * cos_th
            v = bm.verts.new((x, y, z_nominal))
            ring.append(v)
        torso_rings.append(ring)

    mid_start_r = N_RINGS_LOWER
    for r in range(mid_start_r, mid_start_r + N_RINGS_MID):
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

    # 3. UPPER CHEST & SHOULDERS WITH CONTINUOUS ERGONOMIC PROFILE
    top_target_coords = [None] * N_COLS

    for i in range(2, 15):
        if i <= 5:
            u_sh = (5 - i) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            # Anatomical shoulder slope: smooth gentle slope at HPS, natural curvature to shoulder tip
            z_drop = slope_drop * (0.35 * u_sh + 0.65 * (u_sh ** 1.2))
            z = z_hps - z_drop
            # Realistic shoulder depth: 3.0 cm at HPS to 4.8 cm at armhole
            y = 0.030 + 0.018 * u_sh
        elif i >= 11:
            u_sh = (i - 11) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            z_drop = slope_drop * (0.35 * u_sh + 0.65 * (u_sh ** 1.2))
            z = z_hps - z_drop
            y = 0.030 + 0.018 * u_sh
        else:
            k = i - 5
            phi = k / 6.0 * math.pi
            x = neck_half_w * math.cos(phi)
            sin_phi = math.sin(phi)
            s_curve = sin_phi ** 1.6
            y = 0.030 + (0.072 - 0.030) * (sin_phi ** 1.3)
            z = z_hps - neck_front_drop * s_curve
        top_target_coords[i] = (x, y, z)

    for i in range(18, 31):
        if i <= 21:
            u_sh = (21 - i) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            z_drop = slope_drop * (0.35 * u_sh + 0.65 * (u_sh ** 1.2))
            z = z_hps - z_drop
            y = -(0.030 + 0.018 * u_sh)
        elif i >= 27:
            u_sh = (i - 27) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            z_drop = slope_drop * (0.35 * u_sh + 0.65 * (u_sh ** 1.2))
            z = z_hps - z_drop
            y = -(0.030 + 0.018 * u_sh)
        else:
            k = i - 21
            phi = k / 6.0 * math.pi
            x = -neck_half_w * math.cos(phi)
            sin_phi = math.sin(phi)
            s_curve = sin_phi ** 1.6
            y = -(0.030 + (0.050 - 0.030) * (sin_phi ** 1.3))
            z = z_hps - neck_back_drop * s_curve
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

                if abs(tx) > neck_half_w:
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

    # 4. SHOULDER SEAMS
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

    # 5. NECK OPENING & COLLAR
    neck_boundary = [top_ring[i] for i in range(5, 12)] + [top_ring[i] for i in range(21, 28)]
    N_neck = len(neck_boundary)

    if neck_type == "polo":
        stand_rise = 0.018
        neck_center_y = 0.005
        stand_ring = []
        for i, vn in enumerate(neck_boundary):
            dy = vn.co.y - neck_center_y
            r_rel = math.hypot(vn.co.x, dy)
            ux = vn.co.x / r_rel if r_rel > 1e-4 else 0.0
            uy = dy / r_rel if r_rel > 1e-4 else 0.0
            stand_ring.append(bm.verts.new((
                vn.co.x + ux * 0.003,
                vn.co.y + uy * 0.003,
                vn.co.z + stand_rise
            )))

        for i in range(N_neck):
            i_next = (i + 1) % N_neck
            face = bm.faces.new([neck_boundary[i], neck_boundary[i_next], stand_ring[i_next], stand_ring[i]])
            u0 = 0.05 + 0.90 * (i / float(N_neck))
            u1 = 0.05 + 0.90 * ((i + 1) / float(N_neck))
            for loop, uv in zip(face.loops, [Vector((u0, 0.93)), Vector((u1, 0.93)), Vector((u1, 0.96)), Vector((u0, 0.96))]):
                loop[uv_layer].uv = uv

        leaf_ring = []
        for i, vs in enumerate(stand_ring):
            dy = vs.co.y - neck_center_y
            r_rel = math.hypot(vs.co.x, dy)
            ux = vs.co.x / r_rel if r_rel > 1e-4 else 0.0
            uy = dy / r_rel if r_rel > 1e-4 else 0.0

            is_front_lapel = (i in [2, 3, 4])
            if is_front_lapel:
                spread_w = 0.038
                drop_z = 0.026
                lx = vs.co.x + (0.012 if vs.co.x > 0 else -0.012)
                ly = vs.co.y + 0.025
                lz = vs.co.z - drop_z
            else:
                spread_w = 0.032
                drop_z = 0.022
                lx = vs.co.x + ux * spread_w
                ly = vs.co.y + uy * spread_w
                lz = vs.co.z - drop_z
            leaf_ring.append(bm.verts.new((lx, ly, lz)))

        for i in range(N_neck):
            i_next = (i + 1) % N_neck
            face = bm.faces.new([stand_ring[i], stand_ring[i_next], leaf_ring[i_next], leaf_ring[i]])
            u0 = 0.05 + 0.90 * (i / float(N_neck))
            u1 = 0.05 + 0.90 * ((i + 1) / float(N_neck))
            for loop, uv in zip(face.loops, [Vector((u0, 0.96)), Vector((u1, 0.96)), Vector((u1, 0.99)), Vector((u0, 0.99))]):
                loop[uv_layer].uv = uv
    else:
        # Crew-neck ribbed trim
        collar_inward = 0.016
        collar_rise = 0.003
        neck_center_y = 0.005

        coll_rings = [neck_boundary]
        c_ring = []
        for vn in neck_boundary:
            dy = vn.co.y - neck_center_y
            r_rel = math.hypot(vn.co.x, dy)
            ux = vn.co.x / r_rel if r_rel > 1e-4 else 0.0
            uy = dy / r_rel if r_rel > 1e-4 else 0.0
            c_ring.append(bm.verts.new((
                vn.co.x - ux * collar_inward,
                vn.co.y - uy * collar_inward,
                vn.co.z + collar_rise
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
                v0 = 0.93 + 0.05 * (cr / 1.0)
                v1 = 0.93 + 0.05 * ((cr + 1) / 1.0)
                for loop, uv in zip(face.loops, [Vector((u0, v0)), Vector((u1, v0)), Vector((u1, v1)), Vector((u0, v1))]):
                    loop[uv_layer].uv = uv

    # 6. SYMMETRICAL DRAPED SLEEVES
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

    N_pts = len(right_ah)
    sleeve_rings_count = 15 if sleeve_type == "long" else 12
    # Natural apparel drape hang angle: 45.0 degrees below horizontal
    drape_deg = 45.0
    drape_rad = math.radians(drape_deg)
    fwd_deg = 3.0
    fwd_rad = math.radians(fwd_deg)

    a_cuff, b_cuff = solve_ellipse_radii(sleeve_opening, 1.15)

    C_ah_r = np.mean([np.array([v.co.x, v.co.y, v.co.z]) for v in right_ah], axis=0)
    w_dir_r = np.array([math.cos(drape_rad), math.sin(fwd_rad), -math.sin(drape_rad)])
    w_unit_r = w_dir_r / np.linalg.norm(w_dir_r)

    u_v_r = np.array([0.0, 0.0, 1.0])
    u_v_r = u_v_r - np.dot(u_v_r, w_unit_r) * w_unit_r
    u_v_r = u_v_r / np.linalg.norm(u_v_r)

    u_u_r = np.cross(u_v_r, w_unit_r)
    u_u_r = u_u_r / np.linalg.norm(u_u_r)

    ah_coords_r = []
    for v in right_ah:
        rel = np.array([v.co.x, v.co.y, v.co.z]) - C_ah_r
        p_u = float(np.dot(rel, u_u_r))
        p_v = float(np.dot(rel, u_v_r))
        phi = math.atan2(p_u, p_v)
        ah_coords_r.append((p_u, p_v, phi))

    prev_ring_r = right_ah
    prev_ring_l = left_ah

    for r_idx in range(1, sleeve_rings_count + 1):
        t = r_idx / float(sleeve_rings_count)
        t_ease = t * t * (3.0 - 2.0 * t)
        gravity_sag = 0.005 * (t ** 1.5)

        cur_ring_r = []
        cur_ring_l = []

        for i in range(N_pts):
            p_u_base, p_v_base, phi = ah_coords_r[i]
            cap_weight = math.cos(phi)
            ring_disp = (sleeve * t) * (1.0 + 0.03 * max(0.0, cap_weight) * (1.0 - t_ease))

            q_u_target = b_cuff * math.sin(phi)
            q_v_target = a_cuff * math.cos(phi)

            c_u = p_u_base * (1.0 - t_ease) + q_u_target * t_ease
            c_v = p_v_base * (1.0 - t_ease) + q_v_target * t_ease

            V_3d_r = C_ah_r + ring_disp * w_unit_r + np.array([0.0, 0.0, -gravity_sag]) + c_u * u_u_r + c_v * u_v_r
            vr = bm.verts.new(tuple(V_3d_r))
            cur_ring_r.append(vr)

            vl = bm.verts.new((-V_3d_r[0], V_3d_r[1], V_3d_r[2]))
            cur_ring_l.append(vl)

        for i in range(N_pts):
            i_next = (i + 1) % N_pts
            face_r = bm.faces.new([prev_ring_r[i], prev_ring_r[i_next], cur_ring_r[i_next], cur_ring_r[i]])
            u_frac0 = i / float(N_pts)
            u_frac1 = (i + 1) / float(N_pts)
            u0 = 0.05 + 0.40 * u_frac0
            u1 = 0.05 + 0.40 * u_frac1
            v0 = 0.01 + 0.06 * ((r_idx - 1) / float(sleeve_rings_count))
            v1 = 0.01 + 0.06 * (r_idx / float(sleeve_rings_count))
            for loop, uv in zip(face_r.loops, [Vector((u0, v0)), Vector((u1, v0)), Vector((u1, v1)), Vector((u0, v1))]):
                loop[uv_layer].uv = uv

        for i in range(N_pts):
            i_next = (i + 1) % N_pts
            face_l = bm.faces.new([prev_ring_l[i_next], prev_ring_l[i], cur_ring_l[i], cur_ring_l[i_next]])
            u_frac0 = i / float(N_pts)
            u_frac1 = (i + 1) / float(N_pts)
            u0 = 0.55 + 0.40 * u_frac0
            u1 = 0.55 + 0.40 * u_frac1
            v0 = 0.01 + 0.06 * ((r_idx - 1) / float(sleeve_rings_count))
            v1 = 0.01 + 0.06 * (r_idx / float(sleeve_rings_count))
            for loop, uv in zip(face_l.loops, [Vector((u1, v0)), Vector((u0, v0)), Vector((u0, v1)), Vector((u1, v1))]):
                loop[uv_layer].uv = uv

        prev_ring_r = cur_ring_r
        prev_ring_l = cur_ring_l

    orphan_verts = [v for v in bm.verts if not v.link_edges]
    if orphan_verts:
        bmesh.ops.delete(bm, geom=orphan_verts, context='VERTS')

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(f"ParametricTshirt_{selected_size}")
    bm.to_mesh(mesh)
    bm.free()

    for poly in mesh.polygons:
        poly.use_smooth = True

    obj = bpy.data.objects.new(f"Garment_{selected_size}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Export GLB with use_selection=True
    bpy.ops.export_scene.gltf(
        filepath=output_glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_normals=True
    )
    print(f"Exported test GLB to {output_glb_path}")
    return {"obj_name": obj.name, "verts": len(mesh.vertices), "faces": len(mesh.polygons)}

if __name__ == "__main__":
    cfg = {
        "measurements": {
            "chest": 1.0668,
            "shoulder": 0.4572,
            "length": 0.7366,
            "sleeve": 0.20955,
            "neck_circ": 0.4318,
            "sleeve_opening": 0.3556
        },
        "garment_type": "regular_tshirt",
        "fit": "regular",
        "sleeve_type": "short",
        "neck_type": "round",
        "selected_size": "M"
    }
    res = build_improved_garment(cfg, "/tmp/improved_crew_test.glb")
    print("Crew Build result:", res)
