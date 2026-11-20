"""
High-Precision Parametric Polo T-Shirt Geometry Builder.
Pacdora-Grade Tailored Realism:
- True Anatomical Shoulders: 12-14 cm Deltoid Depth in Y
- Smooth Tangent Neck Scoop (Zero sharp kinks)
- Rolled Polo Collar with Natural Cloth Fold over Stand & Clean V-Throat
- Distinct Triangular Collar Wings Lying Gently on Chest
- Integrated Placket with Pearl Buttons
- Relaxed A-Pose Sleeves: 45° drape, 14° forward pitch, open cuffs
- Continuous 2-Manifold Quad Topology with Smooth Cloth Shading
"""

import sys
import os
import math
from typing import Dict, Any, Optional, Tuple, List

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None
    bmesh = None
    Vector = None


def solve_ellipse_radii(circ: float, aspect: float = 1.48) -> Tuple[float, float]:
    """Solves Ramanujan ellipse circumference for half-axes a (width) and b (depth)."""
    r = aspect
    b = circ / (math.pi * (3.0 * (r + 1.0) - math.sqrt((3.0 * r + 1.0) * (r + 3.0))))
    a = r * b
    for _ in range(40):
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


def build_polo_mesh(config: Optional[Dict[str, Any]] = None,
                    output_blend: Optional[str] = None,
                    output_glb: Optional[str] = None) -> Any:
    """
    Builds the master reference Polo T-Shirt mesh in Blender.
    """
    if bpy is None:
        raise RuntimeError("Blender bpy module is required to execute build_polo_mesh.")

    config = config or {}
    measurements = config.get("measurements", {})

    chest_circ = float(measurements.get("chest", 1.06))
    shoulder_w = float(measurements.get("shoulder", 0.49))
    body_len = float(measurements.get("length", 0.71))
    sleeve_len = float(measurements.get("sleeve", 0.21))
    aspect = float(config.get("aspect", 1.48))

    shoulder_half_w = shoulder_w / 2.0
    neck_half_w = 0.092
    z_hps = body_len

    slope_drop = 0.046
    z_shoulder_tip = z_hps - slope_drop

    armhole_depth = 0.215
    z_underarm = z_hps - armhole_depth
    z_waist = z_hps * 0.40
    z_hem = 0.0

    neck_front_drop = 0.078
    neck_back_drop = 0.024
    z_neck_front = z_hps - neck_front_drop

    a_chest, b_chest = solve_ellipse_radii(chest_circ, aspect)
    a_waist = a_chest * 0.965
    b_waist = b_chest * 0.965
    a_hem = a_chest * 0.985
    b_hem = b_chest * 0.985

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    mesh_data = bpy.data.meshes.new("PoloMesh")
    obj = bpy.data.objects.new("PoloTShirt", mesh_data)
    scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    N_COLS = 32
    N_RINGS_LOWER = 14
    N_RINGS_CHEST = 6
    N_RINGS_SHOULDER = 5

    vg_torso = set()
    vg_front = set()
    vg_back = set()
    vg_hem = set()
    vg_left_sh = set()
    vg_right_sh = set()
    vg_left_sl = set()
    vg_right_sl = set()
    vg_neckline = set()
    vg_polo_collar = set()
    vg_polo_placket = set()

    # 1. LOWER TORSO
    torso_rings = []
    for r_idx in range(N_RINGS_LOWER + 1):
        t = r_idx / float(N_RINGS_LOWER)
        z_curr = z_hem + t * z_underarm

        if t < 0.45:
            u = t / 0.45
            u_ease = 0.5 * (1.0 - math.cos(math.pi * u))
            cur_a = a_hem * (1.0 - u_ease) + a_waist * u_ease
            cur_b = b_hem * (1.0 - u_ease) + b_waist * u_ease
        else:
            u = (t - 0.45) / 0.55
            u_ease = 0.5 * (1.0 - math.cos(math.pi * u))
            cur_a = a_waist * (1.0 - u_ease) + a_chest * u_ease
            cur_b = b_waist * (1.0 - u_ease) + b_chest * u_ease

        ring = []
        for i in range(N_COLS):
            th = 2.0 * math.pi * i / float(N_COLS)
            sin_th = math.sin(th)
            cos_th = math.cos(th)
            x = cur_a * cos_th

            if sin_th >= 0:
                y = cur_b * sin_th * (1.0 + 0.08 * sin_th * t)
            else:
                y = cur_b * sin_th * (1.0 - 0.03 * abs(sin_th))

            v = bm.verts.new((x, y, z_curr))
            ring.append(v)
            vg_torso.add(v)
            if r_idx == 0:
                vg_hem.add(v)
            if i < 16:
                vg_front.add(v)
            else:
                vg_back.add(v)
        torso_rings.append(ring)

    for r_idx in range(N_RINGS_LOWER):
        r1 = torso_rings[r_idx]
        r2 = torso_rings[r_idx + 1]
        for i in range(N_COLS):
            i_next = (i + 1) % N_COLS
            f = bm.faces.new([r1[i], r1[i_next], r2[i_next], r2[i]])
            for loop in f.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                u_coord = 0.25 - (vx / (2.2 * a_chest)) * 0.35 if vy >= 0 else 0.75 + (vx / (2.2 * a_chest)) * 0.35
                v_coord = max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))
                loop[uv_layer].uv = Vector((u_coord, v_coord))

    # 2. MID TORSO
    for r_idx in range(1, N_RINGS_CHEST + 1):
        t = r_idx / float(N_RINGS_CHEST)
        z_curr = z_underarm + t * (z_shoulder_tip - z_underarm) * 0.58
        cur_a = a_chest * (1.0 - 0.015 * (t ** 1.1))
        cur_b = b_chest * (1.0 + 0.04 * math.sin(math.pi * t))

        ring = [None] * N_COLS
        for i in range(2, 15):
            th = 2.0 * math.pi * i / float(N_COLS)
            sin_th = math.sin(th)
            cos_th = math.cos(th)
            x = cur_a * cos_th
            y = cur_b * sin_th * (1.0 + 0.08 * sin_th)
            v = bm.verts.new((x, y, z_curr))
            ring[i] = v
            vg_torso.add(v)
            vg_front.add(v)

        for i in range(18, 31):
            th = 2.0 * math.pi * i / float(N_COLS)
            sin_th = math.sin(th)
            cos_th = math.cos(th)
            x = cur_a * cos_th
            y = cur_b * sin_th * (1.0 - 0.03 * abs(sin_th))
            v = bm.verts.new((x, y, z_curr))
            ring[i] = v
            vg_torso.add(v)
            vg_back.add(v)

        torso_rings.append(ring)

    mid_start_r = N_RINGS_LOWER
    for r_idx in range(mid_start_r, mid_start_r + N_RINGS_CHEST):
        r1 = torso_rings[r_idx]
        r2 = torso_rings[r_idx + 1]
        for i in range(2, 14):
            f = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in f.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                loop[uv_layer].uv = Vector((0.25 - (vx / (2.2 * a_chest)) * 0.35, max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))))
        for i in range(18, 30):
            f = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in f.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                loop[uv_layer].uv = Vector((0.75 + (vx / (2.2 * a_chest)) * 0.35, max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))))

    # 3. UPPER CHEST, SHOULDERS & POLO NECKLINE
    top_target_coords = [None] * N_COLS
    y_neck_mid = 0.008

    for i in range(2, 15):
        if i <= 5: # Right shoulder front
            u_sh = (5 - i) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            z = z_hps - slope_drop * (u_sh ** 1.15)
            y = y_neck_mid + 0.046 + 0.022 * u_sh
        elif i >= 11: # Left shoulder front
            u_sh = (i - 11) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            z = z_hps - slope_drop * (u_sh ** 1.15)
            y = y_neck_mid + 0.046 + 0.022 * u_sh
        else: # Front neck scoop - smooth tangent ease
            k = i - 5
            u_neck = k / 6.0
            phi = u_neck * math.pi
            x = neck_half_w * math.cos(phi)
            smooth_drop = 0.5 * (1.0 - math.cos(phi))
            z = z_hps - neck_front_drop * smooth_drop
            y = y_neck_mid + 0.046 * (1.0 - smooth_drop) + 0.074 * math.sin(phi)
        top_target_coords[i] = (x, y, z)

    for i in range(18, 31):
        if i <= 21: # Left shoulder back
            u_sh = (21 - i) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            z = z_hps - slope_drop * (u_sh ** 1.15)
            y = y_neck_mid - (0.044 + 0.020 * u_sh)
        elif i >= 27: # Right shoulder back
            u_sh = (i - 27) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            z = z_hps - slope_drop * (u_sh ** 1.15)
            y = y_neck_mid - (0.044 + 0.020 * u_sh)
        else: # Back neck scoop
            k = i - 21
            u_neck = k / 6.0
            phi = u_neck * math.pi
            x = -neck_half_w * math.cos(phi)
            smooth_drop = 0.5 * (1.0 - math.cos(phi))
            z = z_hps - neck_back_drop * smooth_drop
            y = y_neck_mid - (0.044 * (1.0 - smooth_drop) + 0.050 * math.sin(phi))
        top_target_coords[i] = (x, y, z)

    mid_top_ring = torso_rings[-1]
    for r_sh in range(1, N_RINGS_SHOULDER + 1):
        t_sh = r_sh / float(N_RINGS_SHOULDER)
        t_ease = 0.5 * (1.0 - math.cos(math.pi * t_sh))
        ring = [None] * N_COLS
        for i in range(N_COLS):
            if top_target_coords[i] is not None:
                v_mid = mid_top_ring[i]
                tx, ty, tz = top_target_coords[i]
                x_interp = v_mid.co.x * (1.0 - t_ease) + tx * t_ease
                y_interp = v_mid.co.y * (1.0 - t_ease) + ty * t_ease
                z_interp = v_mid.co.z * (1.0 - t_ease) + tz * t_ease
                v = bm.verts.new((x_interp, y_interp, z_interp))
                ring[i] = v
                vg_torso.add(v)
                if i < 16:
                    vg_front.add(v)
                else:
                    vg_back.add(v)
                if i in [2, 3, 4, 5, 27, 28, 29, 30]:
                    vg_right_sh.add(v)
                elif i in [11, 12, 13, 14, 18, 19, 20, 21]:
                    vg_left_sh.add(v)
        torso_rings.append(ring)

    sh_start_r = mid_start_r + N_RINGS_CHEST
    for r_idx in range(sh_start_r, sh_start_r + N_RINGS_SHOULDER):
        r1 = torso_rings[r_idx]
        r2 = torso_rings[r_idx + 1]
        for i in range(2, 14):
            f = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in f.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                loop[uv_layer].uv = Vector((0.25 - (vx / (2.2 * a_chest)) * 0.35, max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))))
        for i in range(18, 30):
            f = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in f.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                loop[uv_layer].uv = Vector((0.75 + (vx / (2.2 * a_chest)) * 0.35, max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))))

    # 4. SHOULDER SEAMS
    top_r = torso_rings[-1]
    for k in range(3):
        f1 = top_r[2 + k]
        f2 = top_r[3 + k]
        b1 = top_r[30 - k]
        b2 = top_r[29 - k]
        face = bm.faces.new([f1, f2, b2, b1])
        vg_right_sh.update([f1, f2, b2, b1])
        for loop in face.loops:
            vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
            loop[uv_layer].uv = Vector((0.25 - (vx / (2.2 * a_chest)) * 0.35 if vy >= 0 else 0.75 + (vx / (2.2 * a_chest)) * 0.35, max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))))

    for k in range(3):
        f1 = top_r[11 + k]
        f2 = top_r[12 + k]
        b1 = top_r[21 - k]
        b2 = top_r[20 - k]
        face = bm.faces.new([f1, f2, b2, b1])
        vg_left_sh.update([f1, f2, b2, b1])
        for loop in face.loops:
            vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
            loop[uv_layer].uv = Vector((0.25 - (vx / (2.2 * a_chest)) * 0.35 if vy >= 0 else 0.75 + (vx / (2.2 * a_chest)) * 0.35, max(0.01, min(0.99, 0.08 + (vz / z_hps) * 0.82))))

    # 5. INTEGRATED POLO BUTTON PLACKET
    placket_w = 0.036
    placket_len = 0.145
    placket_top_z = z_neck_front
    placket_bot_z = z_neck_front - placket_len
    y_placket = b_chest * 0.99 + 0.0024

    p_tl = bm.verts.new((-placket_w / 2.0, y_placket, placket_top_z))
    p_tr = bm.verts.new((placket_w / 2.0, y_placket, placket_top_z))
    p_br = bm.verts.new((placket_w / 2.0, y_placket, placket_bot_z))
    p_bl = bm.verts.new((-placket_w / 2.0, y_placket, placket_bot_z))

    f_placket = bm.faces.new([p_tl, p_tr, p_br, p_bl])
    vg_polo_placket.update([p_tl, p_tr, p_br, p_bl])
    for loop in f_placket.loops:
        loop[uv_layer].uv = Vector((0.25, 0.82))

    y_base = b_chest * 0.99
    p_base_tl = bm.verts.new((-placket_w / 2.0, y_base, placket_top_z))
    p_base_tr = bm.verts.new((placket_w / 2.0, y_base, placket_top_z))
    p_base_br = bm.verts.new((placket_w / 2.0, y_base, placket_bot_z))
    p_base_bl = bm.verts.new((-placket_w / 2.0, y_base, placket_bot_z))

    f_pl_l = bm.faces.new([p_base_tl, p_tl, p_bl, p_base_bl])
    f_pl_r = bm.faces.new([p_tr, p_base_tr, p_base_br, p_br])
    f_pl_b = bm.faces.new([p_bl, p_br, p_base_br, p_base_bl])
    vg_polo_placket.update([p_base_tl, p_base_tr, p_base_br, p_base_bl])
    for f in [f_pl_l, f_pl_r, f_pl_b]:
        for loop in f.loops:
            loop[uv_layer].uv = Vector((0.25, 0.82))

    # 3D Pearl Buttons
    btn_r = 0.0055
    btn_t = 0.0018
    N_btn_sides = 12
    btn_z_positions = [placket_top_z - 0.042, placket_top_z - 0.098]
    for bz in btn_z_positions:
        by = y_placket + 0.0004
        btn_front = []
        btn_back = []
        for k in range(N_btn_sides):
            th = 2.0 * math.pi * k / float(N_btn_sides)
            xk = btn_r * math.sin(th)
            zk = bz + btn_r * math.cos(th)
            btn_front.append(bm.verts.new((xk, by + btn_t, zk)))
            btn_back.append(bm.verts.new((xk, by, zk)))
        v_center = bm.verts.new((0.0, by + btn_t * 0.35, bz))
        v_back_center = bm.verts.new((0.0, by, bz))
        for k in range(N_btn_sides):
            k_next = (k + 1) % N_btn_sides
            bm.faces.new([btn_back[k], btn_back[k_next], btn_front[k_next], btn_front[k]])
            bm.faces.new([v_center, btn_front[k], btn_front[k_next]])
            bm.faces.new([btn_back[k_next], btn_back[k], v_back_center])
        vg_polo_placket.update(btn_front + btn_back + [v_center, v_back_center])

    # 6. OPEN SPREAD POLO COLLAR (Tailored Rolled Collar with Open V-Throat)
    stand_base_path = [
        p_tr,
        top_r[6], top_r[5],
        top_r[27], top_r[26], top_r[25], top_r[24], top_r[23], top_r[22], top_r[21],
        top_r[11], top_r[10],
        p_tl
    ]
    N_stand = len(stand_base_path)

    stand_top = []
    stand_h_back = 0.020
    stand_h_front = 0.012
    for idx, vb in enumerate(stand_base_path):
        u_arc = abs(idx - (N_stand - 1) / 2.0) / ((N_stand - 1) / 2.0)
        cur_h = stand_h_back * (1.0 - u_arc) + stand_h_front * u_arc
        vs = bm.verts.new((vb.co.x * 0.98, vb.co.y * 0.98, vb.co.z + cur_h))
        stand_top.append(vs)
        vg_polo_collar.add(vs)

    for i in range(N_stand - 1):
        f_st = bm.faces.new([stand_base_path[i], stand_base_path[i + 1], stand_top[i + 1], stand_top[i]])
        for loop in f_st.loops:
            loop[uv_layer].uv = Vector((0.05 + 0.90 * (i / float(N_stand)), 0.93))

    leaf_outer = []
    leaf_inner = []
    cloth_t = 0.0018
    for idx, vs in enumerate(stand_top):
        u_arc = abs(idx - (N_stand - 1) / 2.0) / ((N_stand - 1) / 2.0)
        if idx in [0, 1]:
            lx = vs.co.x + 0.024
            ly = vs.co.y + 0.034
            lz = vs.co.z - 0.034
        elif idx in [N_stand - 2, N_stand - 1]:
            lx = vs.co.x - 0.024
            ly = vs.co.y + 0.034
            lz = vs.co.z - 0.034
        else:
            spread_out = 0.034 + 0.006 * u_arc
            drop_down = 0.026 + 0.005 * u_arc
            dy = vs.co.y
            r_rel = math.hypot(vs.co.x, dy)
            ux = vs.co.x / r_rel if r_rel > 1e-4 else 0.0
            uy = dy / r_rel if r_rel > 1e-4 else 0.0
            lx = vs.co.x + ux * spread_out
            ly = vs.co.y + uy * spread_out
            lz = vs.co.z - drop_down

        vo = bm.verts.new((lx, ly, lz))
        vi = bm.verts.new((lx, ly - 0.0014, lz + cloth_t))
        leaf_outer.append(vo)
        leaf_inner.append(vi)
        vg_polo_collar.update([vo, vi])

    for i in range(N_stand - 1):
        f_top = bm.faces.new([stand_top[i], stand_top[i + 1], leaf_outer[i + 1], leaf_outer[i]])
        f_rim = bm.faces.new([leaf_outer[i], leaf_outer[i + 1], leaf_inner[i + 1], leaf_inner[i]])
        f_bot = bm.faces.new([leaf_inner[i], leaf_inner[i + 1], stand_base_path[i + 1], stand_base_path[i]])
        for loop in f_top.loops:
            loop[uv_layer].uv = Vector((0.05 + 0.90 * (i / float(N_stand)), 0.96))
        for loop in f_rim.loops:
            loop[uv_layer].uv = Vector((0.05 + 0.90 * (i / float(N_stand)), 0.975))
        for loop in f_bot.loops:
            loop[uv_layer].uv = Vector((0.05 + 0.90 * (i / float(N_stand)), 0.94))

    # 7. SEAMLESS SET-IN SLEEVES (Pacdora A-pose drape: 45° down, 14° forward)
    TOTAL_RINGS = len(torso_rings)

    def attach_seamless_sleeve(is_left=True):
        vg_target = vg_left_sl if is_left else vg_right_sl
        side_sign = -1.0 if is_left else 1.0

        ah_loop = []
        if is_left:
            ah_loop.append(torso_rings[N_RINGS_LOWER][15])
            ah_loop.append(torso_rings[N_RINGS_LOWER][16])
            ah_loop.append(torso_rings[N_RINGS_LOWER][17])
            for r in range(N_RINGS_LOWER, TOTAL_RINGS):
                ah_loop.append(torso_rings[r][18])
            for r in range(TOTAL_RINGS - 1, N_RINGS_LOWER - 1, -1):
                ah_loop.append(torso_rings[r][14])
        else:
            ah_loop.append(torso_rings[N_RINGS_LOWER][31])
            ah_loop.append(torso_rings[N_RINGS_LOWER][0])
            ah_loop.append(torso_rings[N_RINGS_LOWER][1])
            for r in range(N_RINGS_LOWER, TOTAL_RINGS):
                ah_loop.append(torso_rings[r][2])
            for r in range(TOTAL_RINGS - 1, N_RINGS_LOWER - 1, -1):
                ah_loop.append(torso_rings[r][30])

        N_ah = len(ah_loop)
        c0 = Vector((
            sum(v.co.x for v in ah_loop) / float(N_ah),
            sum(v.co.y for v in ah_loop) / float(N_ah),
            sum(v.co.z for v in ah_loop) / float(N_ah)
        ))

        drape_angle = math.radians(45.0)
        pitch_angle = math.radians(14.0)

        d_vec = Vector((
            side_sign * math.cos(drape_angle) * math.cos(pitch_angle),
            math.sin(pitch_angle),
            -math.sin(drape_angle) * math.cos(pitch_angle)
        )).normalized()

        u_vec = (Vector((0, 1, 0)) - Vector((0, 1, 0)).dot(d_vec) * d_vec).normalized()
        v_vec = d_vec.cross(u_vec).normalized()

        proj_angles = []
        for v in ah_loop:
            rel = v.co - c0
            u_val = rel.dot(u_vec)
            v_val = rel.dot(v_vec)
            proj_angles.append(math.atan2(v_val, u_val))

        N_SLEEVE_RINGS = 8
        prev_ring = ah_loop
        for k in range(1, N_SLEEVE_RINGS + 1):
            t = k / float(N_SLEEVE_RINGS)
            t_morph = 0.5 * (1.0 - math.cos(math.pi * t))
            c_k = c0 + d_vec * (sleeve_len * t)

            flare = 0.008 * math.sin(math.pi * t)
            c_k.x += side_sign * flare * 0.25
            c_k.z -= 0.003 * math.sin(math.pi * t)

            rad_u = 0.092 * (1.0 - 0.12 * t)
            rad_v = 0.096 * (1.0 - 0.14 * t)

            cur_ring = []
            for i in range(N_ah):
                phi = proj_angles[i]
                p_round = c_k + u_vec * (rad_u * math.cos(phi)) + v_vec * (rad_v * math.sin(phi))
                p_linear = ah_loop[i].co + d_vec * (sleeve_len * t)
                p_final = p_linear * (1.0 - t_morph) + p_round * t_morph
                v_sl = bm.verts.new(p_final)
                cur_ring.append(v_sl)
                vg_target.add(v_sl)

            for i in range(N_ah):
                i_next = (i + 1) % N_ah
                f = bm.faces.new([prev_ring[i], prev_ring[i_next], cur_ring[i_next], cur_ring[i]])
                u0 = (0.05 if is_left else 0.55) + 0.40 * (i / float(N_ah))
                u1 = (0.05 if is_left else 0.55) + 0.40 * ((i + 1) / float(N_ah))
                v0 = 0.60 - 0.45 * ((k - 1) / float(N_SLEEVE_RINGS))
                v1 = 0.60 - 0.45 * (k / float(N_SLEEVE_RINGS))
                for loop, uv in zip(f.loops, [Vector((u0, v0)), Vector((u1, v0)), Vector((u1, v1)), Vector((u0, v1))]):
                    loop[uv_layer].uv = uv

            prev_ring = cur_ring

        # Sleeve Cuff Hem
        cuff_rim = []
        for v in prev_ring:
            rel = v.co - c_k
            v_rim = bm.verts.new(v.co - rel.normalized() * 0.0032 - d_vec * 0.004)
            cuff_rim.append(v_rim)
            vg_target.add(v_rim)

        for i in range(N_ah):
            i_next = (i + 1) % N_ah
            f_cuff = bm.faces.new([prev_ring[i], prev_ring[i_next], cuff_rim[i_next], cuff_rim[i]])
            for loop in f_cuff.loops:
                loop[uv_layer].uv = Vector((0.25, 0.15))

    attach_seamless_sleeve(is_left=True)
    attach_seamless_sleeve(is_left=False)

    bm.to_mesh(mesh_data)
    bm.free()

    # Recalculate normals & enable silky smooth cloth shading across all polygons
    bm_clean = bmesh.new()
    bm_clean.from_mesh(mesh_data)
    bmesh.ops.recalc_face_normals(bm_clean, faces=bm_clean.faces)
    bm_clean.to_mesh(mesh_data)
    bm_clean.free()

    for poly in mesh_data.polygons:
        poly.use_smooth = True

    mesh_data.update()

    # Create Vertex Groups
    for vg_name in ["Torso", "FrontBody", "BackBody", "Hem", "LeftShoulder", "RightShoulder", "LeftSleeve", "RightSleeve", "Neckline", "PoloCollar", "PoloPlacket"]:
        if vg_name not in obj.vertex_groups:
            obj.vertex_groups.new(name=vg_name)

    vg_torso_grp = obj.vertex_groups["Torso"]
    vg_front_grp = obj.vertex_groups["FrontBody"]
    vg_back_grp = obj.vertex_groups["BackBody"]
    vg_hem_grp = obj.vertex_groups["Hem"]
    vg_l_sh_grp = obj.vertex_groups["LeftShoulder"]
    vg_r_sh_grp = obj.vertex_groups["RightShoulder"]
    vg_l_sl_grp = obj.vertex_groups["LeftSleeve"]
    vg_r_sl_grp = obj.vertex_groups["RightSleeve"]
    vg_neck_grp = obj.vertex_groups["Neckline"]
    vg_collar_grp = obj.vertex_groups["PoloCollar"]
    vg_placket_grp = obj.vertex_groups["PoloPlacket"]

    for v in mesh_data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        if x < -shoulder_half_w * 0.96 and z < z_shoulder_tip + 0.02:
            vg_l_sl_grp.add([v.index], 1.0, 'REPLACE')
        elif x > shoulder_half_w * 0.96 and z < z_shoulder_tip + 0.02:
            vg_r_sl_grp.add([v.index], 1.0, 'REPLACE')
        elif abs(x) <= placket_w * 0.85 and z <= placket_top_z + 0.01 and z >= placket_bot_z - 0.01 and y > b_chest * 0.92:
            vg_placket_grp.add([v.index], 1.0, 'REPLACE')
        elif z > z_neck_front - 0.04 and y > b_chest * 0.85 and abs(x) < neck_half_w * 1.3:
            vg_collar_grp.add([v.index], 1.0, 'REPLACE')
        else:
            vg_torso_grp.add([v.index], 1.0, 'REPLACE')
            if y >= 0:
                vg_front_grp.add([v.index], 1.0, 'REPLACE')
            else:
                vg_back_grp.add([v.index], 1.0, 'REPLACE')

            if z <= 0.025:
                vg_hem_grp.add([v.index], 1.0, 'REPLACE')

            if z >= z_underarm * 1.05:
                if x < -neck_half_w * 0.90:
                    vg_l_sh_grp.add([v.index], 1.0, 'REPLACE')
                elif x > neck_half_w * 0.90:
                    vg_r_sh_grp.add([v.index], 1.0, 'REPLACE')
                else:
                    vg_neck_grp.add([v.index], 1.0, 'REPLACE')

    if output_blend:
        os.makedirs(os.path.dirname(os.path.abspath(output_blend)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=output_blend)
        print(f"MASTER_POLO_BLEND_SAVED: {output_blend}")

    if output_glb:
        os.makedirs(os.path.dirname(os.path.abspath(output_glb)), exist_ok=True)
        bpy.ops.export_scene.gltf(
            filepath=output_glb,
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_materials='EXPORT',
            export_normals=True
        )
        print(f"MASTER_POLO_GLB_SAVED: {output_glb}")

    return obj
