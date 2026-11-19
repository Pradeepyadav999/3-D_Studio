"""Parametric 3D T-shirt Generator for Blender Headless Worker.
Generates genuine, realistic, regular-fit 3D garment geometry with anatomical proportions,
natural shoulder width & slope, relaxed round crew neckline, and 100% symmetrical draped sleeves.
"""
import sys
import os
import json
import math
import argparse
import numpy as np

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None
    bmesh = None
    Vector = None


def solve_ellipse_radii(circ: float, aspect: float = 2.45):
    """
    Ramanujan's ellipse perimeter approximation solver:
    Perimeter C ≈ π [ 3(a + b) - √((3a + b)(a + 3b)) ]
    where a = aspect * b.
    Solves for semi-major axis 'a' (half-width) and semi-minor axis 'b' (half-depth).
    """
    r = float(aspect)
    # Initial estimate: circle with equivalent perimeter
    b = circ / (2.0 * math.pi * math.sqrt((r * r + 1.0) / 2.0))
    a = r * b

    for _ in range(35):
        curr_c = math.pi * (3.0 * (a + b) - math.sqrt((3.0 * a + b) * (a + 3.0 * b)))
        error = curr_c - circ
        if abs(error) < 1e-8:
            break
        delta = 1e-6
        b_plus = b + delta
        a_plus = r * b_plus
        c_plus = math.pi * (3.0 * (a_plus + b_plus) - math.sqrt((3.0 * a_plus + b_plus) * (a_plus + 3.0 * b_plus)))
        dc_db = (c_plus - curr_c) / delta
        b = b - error / dc_db
        a = r * b

    return a, b


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

    # Dimensions in meters - realistic apparel baseline
    chest = float(measurements.get("chest", 1.06))
    shoulder = float(measurements.get("shoulder", 0.49))
    length = float(measurements.get("length", 0.71))
    sleeve = float(measurements.get("sleeve", 0.21 if sleeve_type == "short" else 0.64))

    # Natural apparel drape aspect ratio (width-to-depth)
    # Human athletic torso cross-section: broad chest (~46cm) and realistic depth (~18.7cm)
    if fit == "slim":
        waist_default = chest * 0.92
        hem_default = chest * 0.95
        aspect = 2.38
    elif fit == "relaxed":
        waist_default = chest * 0.98
        hem_default = chest * 1.01
        aspect = 2.52
    else:  # regular fit
        waist_default = chest * 0.96
        hem_default = chest * 0.98
        aspect = 2.45

    waist = float(measurements.get("waist") or waist_default)
    hem = float(measurements.get("hem") or hem_default)
    sleeve_opening = float(measurements.get("sleeve_opening") or (chest * 0.35 if sleeve_type == "short" else chest * 0.25))

    # Calculate cross-section radii
    a_hem, b_hem = solve_ellipse_radii(hem, aspect * 0.97)
    a_waist, b_waist = solve_ellipse_radii(waist, aspect)
    a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.01)

    # Vertical landmarks - dynamically derived from length and shoulder measurements
    z_hem = 0.0
    z_waist = length * 0.38
    armhole_depth = float(measurements.get("armhole_depth") or max(0.18, shoulder * 0.43))
    z_underarm = length - armhole_depth

    # Landmark dimensions - fully parametric from user size card
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
        # Anatomically proportional round crew-neck: 41% of shoulder half-width
        neck_half_w = shoulder_half_w * 0.41

    z_hps = length
    # Natural relaxed anatomical shoulder slope: 14.5 degrees (~3.6 cm drop from HPS to shoulder tip)
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(14.5))
    z_shoulder_tip = z_hps - slope_drop

    neck_front_drop = float(measurements.get("neck_drop") or 0.082)
    neck_back_drop = 0.024
    z_neck_front_base = z_hps - neck_front_drop
    z_neck_back_base = z_hps - neck_back_drop

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # GRID TOPOLOGY RESOLUTION
    # 32 perimeter columns: front 2..14, back 18..30, armhole openings at sides
    N_COLS = 32
    N_RINGS_LOWER = 12
    N_RINGS_MID = 4
    N_RINGS_TOP = 4

    torso_rings = []

    # 1. LOWER TORSO: Hem to Underarm (Horizontal closed rings)
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

        # Subtle organic drape wave along torso flanks (Pacdora 3D realism)
        # Symmetrical across sagittal plane (sin_th is symmetrical, cos_th odd)
        # Peaks between waist and underarm, vanishes at hem and underarm ring 12
        drape_env = math.sin(math.pi * t) if (0.0 < t < 1.0) else 0.0

        ring = []
        for i in range(N_COLS):
            theta = 2.0 * math.pi * i / N_COLS
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)

            if sin_th > 0:
                y = cur_b * sin_th * (1.0 + 0.03 * sin_th) + 0.004 * sin_th
                vz = z_nominal - hem_arc_drop * (sin_th ** 2)
            else:
                y = cur_b * sin_th * (1.0 - 0.02 * abs(sin_th))
                vz = z_nominal - hem_arc_drop * 0.7 * (sin_th ** 2)

            # Apply subtle drape wave only on intermediate rings 1..11 (preserving exact ring 0 and ring 12)
            if 0 < r < N_RINGS_LOWER:
                w_y = 0.0016 * drape_env * math.sin(3.0 * theta)
                w_x = 0.0010 * drape_env * math.cos(2.0 * theta)
                w_z = 0.0008 * drape_env * math.sin(2.0 * theta)
                y += w_y
                vz += w_z
                x = cur_a * cos_th + w_x
            else:
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

    # 2. MID-CHEST REGION (Between Underarm and Neck Drop Base)
    # Broad, convex pectoral contour smoothly transitioning to armscye
    for r in range(1, N_RINGS_MID + 1):
        t_mid = r / float(N_RINGS_MID)
        z_nominal = z_underarm + t_mid * (z_neck_front_base - z_underarm)

        scye_indent = 0.010 * math.sin(math.pi * (t_mid * 0.7))
        cur_a = a_chest - scye_indent
        cur_b = b_chest * (1.0 - 0.08 * t_mid)

        # Natural anatomical chest fullness & thoracic curvature
        pectoral_fullness = 0.0035 * math.sin(math.pi * t_mid)

        ring = []
        for i in range(N_COLS):
            theta = 2.0 * math.pi * i / N_COLS
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)

            if sin_th > 0:
                y = cur_b * sin_th * (1.0 + 0.03 * sin_th) + 0.005 * sin_th + pectoral_fullness * (sin_th ** 2)
            else:
                y = cur_b * sin_th * (1.0 - 0.02 * abs(sin_th)) - 0.0018 * pectoral_fullness * (abs(sin_th) ** 1.5)

            x = cur_a * cos_th
            v = bm.verts.new((x, y, z_nominal))
            ring.append(v)
        torso_rings.append(ring)

    # Stitch mid-chest panels
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

    # 5. NECK OPENING & COLLAR (Round Crew-Neck vs Authentic Turned-Down Polo Collar)
    neck_boundary = [top_ring[i] for i in range(5, 12)] + [top_ring[i] for i in range(21, 28)]
    N_neck = len(neck_boundary)

    if neck_type == "polo":
        # Authentic tailored polo collar: stand + turned-down spread collar leaf with 3D thickness
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

        # Stitch collar stand
        for i in range(N_neck):
            i_next = (i + 1) % N_neck
            face = bm.faces.new([neck_boundary[i], neck_boundary[i_next], stand_ring[i_next], stand_ring[i]])
            face.material_index = 0
            u0 = 0.05 + 0.90 * (i / float(N_neck))
            u1 = 0.05 + 0.90 * ((i + 1) / float(N_neck))
            for loop, uv in zip(face.loops, [Vector((u0, 0.93)), Vector((u1, 0.93)), Vector((u1, 0.96)), Vector((u0, 0.96))]):
                loop[uv_layer].uv = uv

        # Turned-down spread collar leaf with genuine 3D cloth thickness (outer and inner shell)
        leaf_ring_outer = []
        leaf_ring_inner = []
        for i, vs in enumerate(stand_ring):
            dy = vs.co.y - neck_center_y
            r_rel = math.hypot(vs.co.x, dy)
            ux = vs.co.x / r_rel if r_rel > 1e-4 else 0.0
            uy = dy / r_rel if r_rel > 1e-4 else 0.0

            is_front_lapel = (i in [2, 3, 4])  # Pt 7, 8, 9 (front spread points)
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

            leaf_ring_outer.append(bm.verts.new((lx, ly, lz)))
            # Inner layer with 1.4 mm cloth thickness
            leaf_ring_inner.append(bm.verts.new((lx - ux * 0.0014, ly - uy * 0.0014, lz + 0.0014)))

        # Stitch collar leaf outer visible face
        for i in range(N_neck):
            i_next = (i + 1) % N_neck
            face_top = bm.faces.new([stand_ring[i], stand_ring[i_next], leaf_ring_outer[i_next], leaf_ring_outer[i]])
            face_top.material_index = 0
            u0 = 0.05 + 0.90 * (i / float(N_neck))
            u1 = 0.05 + 0.90 * ((i + 1) / float(N_neck))
            for loop, uv in zip(face_top.loops, [Vector((u0, 0.96)), Vector((u1, 0.96)), Vector((u1, 0.99)), Vector((u0, 0.99))]):
                loop[uv_layer].uv = uv

            # Stitch collar folded hem rim edge (giving authentic 3D cloth thickness)
            face_rim = bm.faces.new([leaf_ring_outer[i], leaf_ring_outer[i_next], leaf_ring_inner[i_next], leaf_ring_inner[i]])
            face_rim.material_index = 0
            for loop, uv in zip(face_rim.loops, [Vector((u0, 0.985)), Vector((u1, 0.985)), Vector((u1, 0.99)), Vector((u0, 0.99))]):
                loop[uv_layer].uv = uv

            # Stitch collar underside face
            face_bot = bm.faces.new([leaf_ring_inner[i], leaf_ring_inner[i_next], stand_ring[i_next], stand_ring[i]])
            face_bot.material_index = 0
            for loop, uv in zip(face_bot.loops, [Vector((u0, 0.95)), Vector((u1, 0.95)), Vector((u1, 0.96)), Vector((u0, 0.96))]):
                loop[uv_layer].uv = uv

        # 3D Tailored Front Placket Box
        placket_w = 0.038
        placket_len = 0.165
        placket_top_z = z_neck_front_base
        placket_bot_z = z_neck_front_base - placket_len

        # Estimate torso Y surface along placket
        y_placket_base = b_chest * 0.96
        y_placket_face = y_placket_base + 0.0022  # 2.2 mm raised relief

        p_tl = bm.verts.new((-placket_w / 2.0, y_placket_face, placket_top_z))
        p_tr = bm.verts.new((placket_w / 2.0, y_placket_face, placket_top_z))
        p_br = bm.verts.new((placket_w / 2.0, y_placket_face, placket_bot_z))
        p_bl = bm.verts.new((-placket_w / 2.0, y_placket_face, placket_bot_z))

        face_placket = bm.faces.new([p_tl, p_tr, p_br, p_bl])
        face_placket.material_index = 0
        face_placket.loops[0][uv_layer].uv = Vector((0.265 - 0.016, 0.88))
        face_placket.loops[1][uv_layer].uv = Vector((0.265 + 0.016, 0.88))
        face_placket.loops[2][uv_layer].uv = Vector((0.265 + 0.016, 0.71))
        face_placket.loops[3][uv_layer].uv = Vector((0.265 - 0.016, 0.71))

        # Placket border bevel rims connecting down to torso surface
        p_base_tl = bm.verts.new((-placket_w / 2.0, y_placket_base, placket_top_z))
        p_base_tr = bm.verts.new((placket_w / 2.0, y_placket_base, placket_top_z))
        p_base_br = bm.verts.new((placket_w / 2.0, y_placket_base, placket_bot_z))
        p_base_bl = bm.verts.new((-placket_w / 2.0, y_placket_base, placket_bot_z))

        f_pw_l = bm.faces.new([p_base_tl, p_tl, p_bl, p_base_bl])
        f_pw_r = bm.faces.new([p_tr, p_base_tr, p_base_br, p_br])
        f_pw_b = bm.faces.new([p_bl, p_br, p_base_br, p_base_bl])
        for f in [f_pw_l, f_pw_r, f_pw_b]:
            f.material_index = 0
            for loop in f.loops:
                loop[uv_layer].uv = Vector((0.265, 0.78))

        # Individual 3D Button Meshes (12-sided cylinder discs with rim bevel and recessed center)
        button_count = int(config.get("button_count") or 2)
        if button_count <= 0:
            button_count = 2

        btn_r = 0.0055  # 11 mm diameter
        btn_t = 0.0018  # 1.8 mm thickness
        N_btn_sides = 12

        for b_idx in range(button_count):
            if button_count >= 3:
                zb = placket_top_z - 0.030 - b_idx * 0.050
            else:
                zb = placket_top_z - 0.040 - b_idx * 0.065
            yb = y_placket_face + 0.0004
            xb = 0.0

            front_b_verts = []
            back_b_verts = []
            for k in range(N_btn_sides):
                th = 2.0 * math.pi * k / float(N_btn_sides)
                x_k = xb + btn_r * math.sin(th)
                z_k = zb + btn_r * math.cos(th)
                front_b_verts.append(bm.verts.new((x_k, yb + btn_t, z_k)))
                back_b_verts.append(bm.verts.new((x_k, yb, z_k)))

            v_btn_center = bm.verts.new((xb, yb + btn_t * 0.40, zb))
            v_btn_back_center = bm.verts.new((xb, yb, zb))

            for k in range(N_btn_sides):
                k_next = (k + 1) % N_btn_sides
                # Side wall quad
                f_bs = bm.faces.new([back_b_verts[k], back_b_verts[k_next], front_b_verts[k_next], front_b_verts[k]])
                f_bs.material_index = 1
                for loop in f_bs.loops:
                    loop[uv_layer].uv = Vector((0.95, 0.95))

                # Front recessed pie wedge
                f_bf = bm.faces.new([v_btn_center, front_b_verts[k], front_b_verts[k_next]])
                f_bf.material_index = 1
                for loop in f_bf.loops:
                    loop[uv_layer].uv = Vector((0.95, 0.95))

                # Back cap triangle
                f_bb = bm.faces.new([back_b_verts[k_next], back_b_verts[k], v_btn_back_center])
                f_bb.material_index = 1
                for loop in f_bb.loops:
                    loop[uv_layer].uv = Vector((0.95, 0.95))

    else:
        # Authentic 3D Toroidal Crew-Neck Collar Ribband with Double-Layered Cloth Thickness (Pacdora Realism)
        # 1. Outer collar ribband rising upward and angled inward (~1.5 cm width)
        # 2. Rolled collar rim edge with 2.0 mm cloth thickness
        # 3. Inner collar underside descending into the shirt interior
        # 4. 100% Hollow round neck opening (zero caps)
        collar_rise = 0.014
        collar_inward = 0.012
        cloth_thickness = 0.0020  # 2.0 mm double-layer cloth thickness
        neck_center_y = 0.005

        c_outer = []
        c_rim = []
        c_inner = []

        for vn in neck_boundary:
            dy = vn.co.y - neck_center_y
            r_rel = math.hypot(vn.co.x, dy)
            ux = vn.co.x / r_rel if r_rel > 1e-4 else 0.0
            uy = dy / r_rel if r_rel > 1e-4 else 0.0

            # Outer collar ribband top edge
            vo = bm.verts.new((
                vn.co.x - ux * collar_inward,
                vn.co.y - uy * collar_inward,
                vn.co.z + collar_rise
            ))
            c_outer.append(vo)

            # Rolled collar rim (top folded edge)
            vr = bm.verts.new((
                vo.co.x - ux * cloth_thickness,
                vo.co.y - uy * cloth_thickness,
                vo.co.z - 0.0008
            ))
            c_rim.append(vr)

            # Inner collar underside (interior cloth layer descending into shirt)
            vi = bm.verts.new((
                vn.co.x - ux * (collar_inward * 0.70 + cloth_thickness),
                vn.co.y - uy * (collar_inward * 0.70 + cloth_thickness),
                vn.co.z - 0.004
            ))
            c_inner.append(vi)

        # Stitch 1: Outer Collar Ribband Face (from body neck_boundary to outer top edge)
        for i in range(N_neck):
            i_next = (i + 1) % N_neck
            face_out = bm.faces.new([neck_boundary[i], neck_boundary[i_next], c_outer[i_next], c_outer[i]])
            face_out.material_index = 0
            u0 = 0.05 + 0.90 * (i / float(N_neck))
            u1 = 0.05 + 0.90 * ((i + 1) / float(N_neck))
            for loop, uv in zip(face_out.loops, [Vector((u0, 0.935)), Vector((u1, 0.935)), Vector((u1, 0.965)), Vector((u0, 0.965))]):
                loop[uv_layer].uv = uv

        # Stitch 2: Rolled Top Rim Face (giving authentic 3D cloth thickness at the neck rim)
        for i in range(N_neck):
            i_next = (i + 1) % N_neck
            face_rim = bm.faces.new([c_outer[i], c_outer[i_next], c_rim[i_next], c_rim[i]])
            face_rim.material_index = 0
            u0 = 0.05 + 0.90 * (i / float(N_neck))
            u1 = 0.05 + 0.90 * ((i + 1) / float(N_neck))
            for loop, uv in zip(face_rim.loops, [Vector((u0, 0.965)), Vector((u1, 0.965)), Vector((u1, 0.980)), Vector((u0, 0.980))]):
                loop[uv_layer].uv = uv

        # Stitch 3: Inner Collar Underside Face (interior cloth wall visible inside hollow neck)
        for i in range(N_neck):
            i_next = (i + 1) % N_neck
            face_in = bm.faces.new([c_rim[i], c_rim[i_next], c_inner[i_next], c_inner[i]])
            face_in.material_index = 0
            u0 = 0.05 + 0.90 * (i / float(N_neck))
            u1 = 0.05 + 0.90 * ((i + 1) / float(N_neck))
            for loop, uv in zip(face_in.loops, [Vector((u0, 0.980)), Vector((u1, 0.980)), Vector((u1, 0.950)), Vector((u0, 0.950))]):
                loop[uv_layer].uv = uv

    # 6. SYMMETRICAL NATURAL DRAPED SLEEVES (100% Guaranteed Bilateral Symmetry)
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

    # Compute Right Sleeve Reference Geometry
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

            # Left sleeve: EXACT bilateral reflection across sagittal X=0 plane (-x, y, z)
            vl = bm.verts.new((-V_3d_r[0], V_3d_r[1], V_3d_r[2]))
            cur_ring_l.append(vl)

        # Stitch Right Sleeve faces
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

        # Stitch Left Sleeve faces (mirrored orientation: i_next before i for outward normal)
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

    # 6B. SLEEVE CUFF TURNED-UP FOLDED HEMS WITH 3D CLOTH THICKNESS (100% Hollow)
    # Rolled outer rim + 1.8 cm interior turned-up hem shell with 1.4 mm cloth thickness
    C_cuff_r = np.mean([np.array([v.co.x, v.co.y, v.co.z]) for v in cur_ring_r], axis=0)
    cuff_rim_r = []
    cuff_inner_r = []
    cuff_rim_l = []
    cuff_inner_l = []

    cuff_thickness = 0.0014  # 1.4 mm cloth thickness
    cuff_fold_depth = 0.018  # 1.8 cm turned-up hem depth

    for i in range(N_pts):
        vr = cur_ring_r[i]
        d_vec = C_cuff_r - np.array([vr.co.x, vr.co.y, vr.co.z])
        d_norm = np.linalg.norm(d_vec)
        u_rad = d_vec / d_norm if d_norm > 1e-4 else np.array([0.0, 0.0, 0.0])

        # Right cuff rim
        V_rim_r = np.array([vr.co.x, vr.co.y, vr.co.z]) + 0.0008 * w_unit_r + cuff_thickness * u_rad
        vr_rim = bm.verts.new(tuple(V_rim_r))
        cuff_rim_r.append(vr_rim)

        # Right cuff interior turned-up hem (extending back up inside sleeve)
        V_inner_r = V_rim_r - cuff_fold_depth * w_unit_r + cuff_thickness * u_rad
        vr_inner = bm.verts.new(tuple(V_inner_r))
        cuff_inner_r.append(vr_inner)

        # Left cuff rim (exact bilateral reflection: -x, y, z)
        vl_rim = bm.verts.new((-V_rim_r[0], V_rim_r[1], V_rim_r[2]))
        cuff_rim_l.append(vl_rim)

        # Left cuff interior hem
        vl_inner = bm.verts.new((-V_inner_r[0], V_inner_r[1], V_inner_r[2]))
        cuff_inner_l.append(vl_inner)

    # Stitch Right Sleeve Cuff Rim & Interior Hem
    for i in range(N_pts):
        i_next = (i + 1) % N_pts
        # Rolled rim face
        f_rim_r = bm.faces.new([cur_ring_r[i], cur_ring_r[i_next], cuff_rim_r[i_next], cuff_rim_r[i]])
        f_rim_r.material_index = 0
        u0 = 0.05 + 0.40 * (i / float(N_pts))
        u1 = 0.05 + 0.40 * ((i + 1) / float(N_pts))
        for loop, uv in zip(f_rim_r.loops, [Vector((u0, 0.07)), Vector((u1, 0.07)), Vector((u1, 0.075)), Vector((u0, 0.075))]):
            loop[uv_layer].uv = uv

        # Interior turned-up hem face
        f_in_r = bm.faces.new([cuff_rim_r[i], cuff_rim_r[i_next], cuff_inner_r[i_next], cuff_inner_r[i]])
        f_in_r.material_index = 0
        for loop, uv in zip(f_in_r.loops, [Vector((u0, 0.075)), Vector((u1, 0.075)), Vector((u1, 0.065)), Vector((u0, 0.065))]):
            loop[uv_layer].uv = uv

    # Stitch Left Sleeve Cuff Rim & Interior Hem (mirrored winding for outward normal)
    for i in range(N_pts):
        i_next = (i + 1) % N_pts
        # Rolled rim face
        f_rim_l = bm.faces.new([cur_ring_l[i_next], cur_ring_l[i], cuff_rim_l[i], cuff_rim_l[i_next]])
        f_rim_l.material_index = 0
        u0 = 0.55 + 0.40 * (i / float(N_pts))
        u1 = 0.55 + 0.40 * ((i + 1) / float(N_pts))
        for loop, uv in zip(f_rim_l.loops, [Vector((u1, 0.07)), Vector((u0, 0.07)), Vector((u0, 0.075)), Vector((u1, 0.075))]):
            loop[uv_layer].uv = uv

        # Interior turned-up hem face
        f_in_l = bm.faces.new([cuff_inner_l[i_next], cuff_inner_l[i], cuff_rim_l[i], cuff_rim_l[i_next]])
        f_in_l.material_index = 0
        for loop, uv in zip(f_in_l.loops, [Vector((u1, 0.065)), Vector((u0, 0.065)), Vector((u0, 0.075)), Vector((u1, 0.075))]):
            loop[uv_layer].uv = uv

    # 6C. BOTTOM HEM INTERIOR TURNED-UP FOLDED HEM (100% Hollow Opening)
    # Turned-up interior hem shell (2.0 cm depth, 1.4 mm cloth thickness)
    # Uses dedicated boundary verts so torso_rings[0..12] vertex indexing is 100% preserved
    hem_outer = torso_rings[0]
    hem_edge = []
    hem_rim = []
    hem_inner = []
    hem_thickness = 0.0014
    hem_fold_depth = 0.020

    for i in range(N_COLS):
        vo = hem_outer[i]
        theta = 2.0 * math.pi * i / N_COLS
        sin_th = math.sin(theta)
        cos_th = math.cos(theta)

        inward_x = -cos_th * hem_thickness
        inward_y = -sin_th * hem_thickness

        # Outer edge junction vert (spatially coincident with hem_outer)
        v_edge = bm.verts.new((vo.co.x, vo.co.y, vo.co.z))
        hem_edge.append(v_edge)

        # Rolled bottom hem rim
        v_rim = bm.verts.new((
            vo.co.x + inward_x * 0.7,
            vo.co.y + inward_y * 0.7,
            vo.co.z - 0.0006
        ))
        hem_rim.append(v_rim)

        # Interior hem shell rising +2.0 cm inside the torso
        v_in = bm.verts.new((
            vo.co.x + inward_x * 1.4,
            vo.co.y + inward_y * 1.4,
            vo.co.z + hem_fold_depth
        ))
        hem_inner.append(v_in)

    for i in range(N_COLS):
        i_next = (i + 1) % N_COLS
        is_front = (0 <= i < 16)
        u_coord = 0.265 - (hem_edge[i].co.x / (2.2 * a_chest)) * 0.38 if is_front else 0.735 + (hem_edge[i].co.x / (2.2 * a_chest)) * 0.38

        # Rolled bottom rim quad (outward normal)
        f_rim = bm.faces.new([hem_edge[i_next], hem_edge[i], hem_rim[i], hem_rim[i_next]])
        f_rim.material_index = 0
        for loop in f_rim.loops:
            loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), 0.075))

        # Interior turned-up hem quad (inward normal)
        f_in = bm.faces.new([hem_rim[i_next], hem_rim[i], hem_inner[i], hem_inner[i_next]])
        f_in.material_index = 0
        for loop in f_in.loops:
            loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), 0.085))

    # 7. MESH VALIDATION & NORMALS
    # Remove any unlinked orphan vertices before final validation
    orphan_verts = [v for v in bm.verts if not v.link_edges]
    if orphan_verts:
        bmesh.ops.delete(bm, geom=orphan_verts, context='VERTS')

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(f"ParametricTshirt_{selected_size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(f"Garment_{selected_size}", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    for poly in mesh.polygons:
        poly.use_smooth = True

    # PBR Material with optional genuine product texture, normal map, roughness map, or base color
    texture_path = config.get("texture_path")
    normal_path = config.get("normal_path")
    roughness_path = config.get("roughness_path")
    base_color_hex = config.get("base_color_hex")
    fabric_texture_type = config.get("fabric_texture_type", "cotton_jersey")

    mat = bpy.data.materials.new(name="GarmentMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new('ShaderNodeOutputMaterial')
    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Roughness'].default_value = 0.88 if (neck_type == "polo" or fabric_texture_type == "cotton_pique") else 0.84
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

    # 1. Attach Base Color map (when attached, set factor to pure white so glTF does not multiply/darken artwork)
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
        node_bsdf.inputs['Base Color'].default_value = (0.86, 0.86, 0.88, 1.0)

    # 2. Attach PBR Normal Map
    if normal_path and os.path.exists(normal_path):
        node_norm = nodes.new('ShaderNodeNormalMap')
        node_norm.inputs['Strength'].default_value = 0.85
        node_norm_tex = nodes.new('ShaderNodeTexImage')
        node_norm_tex.image = bpy.data.images.load(os.path.abspath(normal_path))
        node_norm_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(node_norm_tex.outputs['Color'], node_norm.inputs['Color'])
        links.new(node_norm.outputs['Normal'], node_bsdf.inputs['Normal'])

    # 3. Attach PBR Roughness Map
    if roughness_path and os.path.exists(roughness_path):
        node_rough_tex = nodes.new('ShaderNodeTexImage')
        node_rough_tex.image = bpy.data.images.load(os.path.abspath(roughness_path))
        node_rough_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(node_rough_tex.outputs['Color'], node_bsdf.inputs['Roughness'])

    obj.data.materials.append(mat)

    # Dedicated Button Material (Pearl button with subtle specular sheen)
    if neck_type == "polo":
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
        "garment_type": garment_type,
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
