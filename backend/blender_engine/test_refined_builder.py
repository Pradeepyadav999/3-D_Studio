"""
Test and refine Plain Crew and Polo master meshes.
"""
import bpy
import bmesh
from mathutils import Vector
import math
import os

def build_refined_crew(output_blend, output_glb):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    
    chest_circ = 1.04
    shoulder_w = 0.46
    body_len = 0.70
    sleeve_len = 0.20
    aspect = 1.55
    
    shoulder_half_w = shoulder_w / 2.0
    neck_half_w = 0.092
    z_hps = body_len
    
    slope_drop = 0.045
    z_shoulder_tip = z_hps - slope_drop
    
    armhole_depth = 0.210
    z_underarm = z_hps - armhole_depth
    z_waist = z_hps * 0.38
    z_hem = 0.0
    
    neck_front_drop = 0.082
    neck_back_drop = 0.024
    z_neck_front = z_hps - neck_front_drop
    
    b_chest = chest_circ / (math.pi * (3.0 * (aspect + 1.0) - math.sqrt((3.0 * aspect + 1.0) * (aspect + 3.0))))
    a_chest = aspect * b_chest
    
    a_waist = a_chest * 0.97
    b_waist = b_chest * 0.97
    a_hem = a_chest * 0.985
    b_hem = b_chest * 0.985
    
    mesh_data = bpy.data.meshes.new("CrewTShirtMesh")
    obj = bpy.data.objects.new("PlainCrewTShirt", mesh_data)
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
    
    # 1. LOWER TORSO RINGS
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
            y = cur_b * sin_th * (1.0 - 0.015 * abs(sin_th))
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

    # 2. MID TORSO (Underarm to Mid-Chest)
    for r_idx in range(1, N_RINGS_CHEST + 1):
        t = r_idx / float(N_RINGS_CHEST)
        z_curr = z_underarm + t * (z_shoulder_tip - z_underarm) * 0.60
        cur_a = a_chest * (1.0 - 0.02 * (t ** 1.2))
        cur_b = b_chest * (1.0 + 0.025 * math.sin(math.pi * t))
        
        ring = [None] * N_COLS
        for i in range(2, 15):
            th = 2.0 * math.pi * i / float(N_COLS)
            sin_th = math.sin(th)
            cos_th = math.cos(th)
            x = cur_a * cos_th
            y = cur_b * sin_th * (1.0 - 0.015 * abs(sin_th))
            v = bm.verts.new((x, y, z_curr))
            ring[i] = v
            vg_torso.add(v)
            vg_front.add(v)
            
        for i in range(18, 31):
            th = 2.0 * math.pi * i / float(N_COLS)
            sin_th = math.sin(th)
            cos_th = math.cos(th)
            x = cur_a * cos_th
            y = cur_b * sin_th * (1.0 - 0.015 * abs(sin_th))
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

    # 3. UPPER CHEST, ANATOMICAL SHOULDERS & NECKLINE
    top_target_coords = [None] * N_COLS
    y_neck_mid = 0.006
    
    # Natural anatomical shoulder curve and soft seam crest
    for i in range(2, 15):
        if i <= 5: # Right shoulder front
            u_sh = (5 - i) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            # Smooth anatomical shoulder slope
            z = z_hps - slope_drop * (u_sh ** 1.25)
            # Gentle crest towards seam line at Y=0.005
            y = y_neck_mid + 0.024 * (1.0 - u_sh * 0.5)
        elif i >= 11: # Left shoulder front
            u_sh = (i - 11) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            z = z_hps - slope_drop * (u_sh ** 1.25)
            y = y_neck_mid + 0.024 * (1.0 - u_sh * 0.5)
        else: # Front neck scoop (smooth elliptical arc)
            k = i - 5
            phi = k / 6.0 * math.pi
            x = neck_half_w * math.cos(phi)
            sin_phi = math.sin(phi)
            z = z_hps - neck_front_drop * (sin_phi ** 1.15)
            y = y_neck_mid + 0.065 * sin_phi
        top_target_coords[i] = (x, y, z)
        
    for i in range(18, 31):
        if i <= 21: # Left shoulder back
            u_sh = (21 - i) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            z = z_hps - slope_drop * (u_sh ** 1.25)
            y = y_neck_mid - 0.024 * (1.0 - u_sh * 0.5)
        elif i >= 27: # Right shoulder back
            u_sh = (i - 27) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            z = z_hps - slope_drop * (u_sh ** 1.25)
            y = y_neck_mid - 0.024 * (1.0 - u_sh * 0.5)
        else: # Back neck scoop (smooth elliptical arc)
            k = i - 21
            phi = k / 6.0 * math.pi
            x = -neck_half_w * math.cos(phi)
            sin_phi = math.sin(phi)
            z = z_hps - neck_back_drop * (sin_phi ** 1.15)
            y = y_neck_mid - 0.040 * sin_phi
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
                    if r_sh == N_RINGS_SHOULDER and 5 <= i <= 11:
                        vg_neckline.add(v)
                else:
                    vg_back.add(v)
                    if r_sh == N_RINGS_SHOULDER and 21 <= i <= 27:
                        vg_neckline.add(v)
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

    # 4. SHOULDER SEAMS (Bridge Front and Back Shoulder Vertices)
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

    # 5. HIGH-DEFINITION RIBBED CREW NECKBAND
    neck_loop = [
        top_r[5], top_r[6], top_r[7], top_r[8], top_r[9], top_r[10], top_r[11],
        top_r[21], top_r[22], top_r[23], top_r[24], top_r[25], top_r[26], top_r[27]
    ]
    N_neck = len(neck_loop)
    
    collar_rise = 0.018
    collar_inward = 0.014
    cloth_t = 0.0028
    neck_cy = 0.006
    
    c_outer = []
    c_rim = []
    c_inner = []
    
    for vn in neck_loop:
        dy = vn.co.y - neck_cy
        r_rel = math.hypot(vn.co.x, dy)
        ux = vn.co.x / r_rel if r_rel > 1e-4 else 0.0
        uy = dy / r_rel if r_rel > 1e-4 else 0.0
        
        vo = bm.verts.new((vn.co.x - ux * collar_inward, vn.co.y - uy * collar_inward, vn.co.z + collar_rise))
        c_outer.append(vo)
        
        vr = bm.verts.new((vo.co.x - ux * cloth_t, vo.co.y - uy * cloth_t, vo.co.z - 0.0010))
        c_rim.append(vr)
        
        vi = bm.verts.new((vn.co.x - ux * (collar_inward * 0.75 + cloth_t), vn.co.y - uy * (collar_inward * 0.75 + cloth_t), vn.co.z - 0.008))
        c_inner.append(vi)
        
        vg_neckline.update([vo, vr, vi])
        
    for i in range(N_neck):
        i_next = (i + 1) % N_neck
        f_out = bm.faces.new([neck_loop[i], neck_loop[i_next], c_outer[i_next], c_outer[i]])
        f_rim = bm.faces.new([c_outer[i], c_outer[i_next], c_rim[i_next], c_rim[i]])
        f_in = bm.faces.new([c_rim[i], c_rim[i_next], c_inner[i_next], c_inner[i]])
        
        u0 = i / float(N_neck)
        u1 = (i + 1) / float(N_neck)
        for loop, uv in zip(f_out.loops, [Vector((u0, 0.93)), Vector((u1, 0.93)), Vector((u1, 0.96)), Vector((u0, 0.96))]):
            loop[uv_layer].uv = uv
        for loop, uv in zip(f_rim.loops, [Vector((u0, 0.96)), Vector((u1, 0.96)), Vector((u1, 0.975)), Vector((u0, 0.975))]):
            loop[uv_layer].uv = uv
        for loop, uv in zip(f_in.loops, [Vector((u0, 0.975)), Vector((u1, 0.975)), Vector((u1, 0.94)), Vector((u0, 0.94))]):
            loop[uv_layer].uv = uv

    # 6. SEAMLESS SET-IN SLEEVES (Pacdora-matched Natural A-pose Drape: 65° down, 9° forward)
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
        
        # Natural A-pose drape angles matching Pacdora:
        # 65 deg down from horizontal, 9 deg forward pitch
        drape_angle = math.radians(65.0)
        pitch_angle = math.radians(9.0)
        
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
            
            # Gentle soft deltoid flare and forearm taper
            flare = 0.008 * math.sin(math.pi * t)
            c_k.x += side_sign * flare * 0.3
            c_k.z -= 0.004 * math.sin(math.pi * t)
            
            rad_u = 0.082 * (1.0 - 0.12 * t)
            rad_v = 0.088 * (1.0 - 0.14 * t)
            
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
            
        # Folded sleeve hem cuff
        cuff_w = 0.020
        c_cuff = c0 + d_vec * (sleeve_len + cuff_w)
        cuff_ring = []
        for i in range(N_ah):
            phi = proj_angles[i]
            p_cf = c_cuff + u_vec * ((rad_u - 0.002) * math.cos(phi)) + v_vec * ((rad_v - 0.002) * math.sin(phi))
            v_cf = bm.verts.new(p_cf)
            cuff_ring.append(v_cf)
            vg_target.add(v_cf)
            
        for i in range(N_ah):
            i_next = (i + 1) % N_ah
            f_cf = bm.faces.new([prev_ring[i], prev_ring[i_next], cuff_ring[i_next], cuff_ring[i]])
            for loop in f_cf.loops:
                loop[uv_layer].uv = Vector((0.05 if is_left else 0.55, 0.12))

    attach_seamless_sleeve(is_left=True)
    attach_seamless_sleeve(is_left=False)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.verts.index_update()
    
    vg_map = {
        "Torso": [v.index for v in vg_torso if v.is_valid],
        "FrontBody": [v.index for v in vg_front if v.is_valid],
        "BackBody": [v.index for v in vg_back if v.is_valid],
        "Hem": [v.index for v in vg_hem if v.is_valid],
        "LeftShoulder": [v.index for v in vg_left_sh if v.is_valid],
        "RightShoulder": [v.index for v in vg_right_sh if v.is_valid],
        "LeftSleeve": [v.index for v in vg_left_sl if v.is_valid],
        "RightSleeve": [v.index for v in vg_right_sl if v.is_valid],
        "Neckline": [v.index for v in vg_neckline if v.is_valid]
    }
    
    bm.to_mesh(mesh_data)
    bm.free()
    
    for group_name, idx_list in vg_map.items():
        grp = obj.vertex_groups.new(name=group_name)
        if idx_list:
            grp.add(idx_list, 1.0, 'REPLACE')
            
    # Smooth shading
    for poly in mesh_data.polygons:
        poly.use_smooth = True
        
    os.makedirs(os.path.dirname(output_blend), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=output_blend)
    bpy.ops.export_scene.gltf(filepath=output_glb, export_format='GLB', use_selection=True)
    print(f"BUILT_CREW_REFINED: {output_blend} and {output_glb}")
    return obj

print("Crew refined function defined.")
