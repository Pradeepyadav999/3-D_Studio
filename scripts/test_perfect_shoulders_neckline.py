"""Test script to implement and verify perfect shoulders and round neckline."""
import os
import sys
import math
import numpy as np

try:
    import bpy
    import bmesh
except ImportError:
    print("Run via Blender")
    sys.exit(1)

def solve_ellipse_radii(circ: float, aspect: float = 1.54):
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

def build_perfect_tshirt(config: dict, output_path: str):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    measurements = config.get("measurements", {})
    chest = float(measurements.get("chest", 0.96))
    shoulder = float(measurements.get("shoulder", 0.40))
    length = float(measurements.get("length", 0.66))
    sleeve = float(measurements.get("sleeve", 0.18))
    fit = config.get("fit", "regular")
    neck_type = config.get("neck_type", "round")
    selected_size = config.get("selected_size", "S")

    # Regular fit dimensions
    aspect = 1.54
    waist_circ = float(measurements.get("waist") or (chest * 0.95))
    hem_circ = float(measurements.get("hem") or (chest * 0.98))
    sleeve_opening = float(measurements.get("sleeve_opening") or (chest * 0.33))

    a_hem, b_hem = solve_ellipse_radii(hem_circ, aspect * 0.97)
    a_waist, b_waist = solve_ellipse_radii(waist_circ, aspect)
    a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.02)

    z_hem = 0.0
    z_waist = length * 0.40
    armhole_depth = max(0.185, shoulder * 0.47)
    z_underarm = length - armhole_depth

    # Shoulder and Neckline landmarks
    shoulder_half_w = shoulder / 2.0  # 0.20 m for Size S
    neck_half_w = 0.078  # 7.8 cm half-width (15.6 cm total neck opening width)
    
    # 14.0 degree anatomical shoulder slope
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(14.0))  # ~0.030 m
    z_hps = length  # 0.66 m
    z_shoulder_tip = z_hps - slope_drop  # ~0.630 m

    # Crew neckline drops
    neck_front_drop = 0.082  # 8.2 cm front scoop for round crew-neck
    neck_back_drop = 0.024   # 2.4 cm back scoop
    neck_front_depth_y = 0.052  # Y forward position of center front collar
    neck_back_depth_y = 0.042   # Y backward position of center back collar

    bm = bmesh.new()

    # Grid Resolution
    N_PERIM = 32
    N_LOWER = 10  # Hem to underarm
    N_UPPER = 8   # Underarm to shoulder

    torso_rings = []

    # 1. LOWER TORSO: Continuous multi-ring tube from hem to underarm
    for r in range(N_LOWER + 1):
        t = r / float(N_LOWER)
        if t < 0.42:
            s = t / 0.42
            s_ease = 0.5 * (1.0 - math.cos(math.pi * s))
            cur_a = a_hem * (1 - s_ease) + a_waist * s_ease
            cur_b = b_hem * (1 - s_ease) + b_waist * s_ease
        else:
            s = (t - 0.42) / 0.58
            s_ease = 0.5 * (1.0 - math.cos(math.pi * s))
            cur_a = a_waist * (1 - s_ease) + a_chest * s_ease
            cur_b = b_waist * (1 - s_ease) + b_chest * s_ease

        z_nominal = z_hem + t * z_underarm
        hem_arc_drop = 0.010 * ((1.0 - t) ** 1.8)

        ring = []
        for i in range(N_PERIM):
            theta = 2.0 * math.pi * i / N_PERIM
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)

            if sin_th > 0:
                y_contour = cur_b * sin_th * (1.0 + 0.06 * sin_th - 0.015 * math.sin(3.0 * theta)) + 0.005 * sin_th
                vz = z_nominal - hem_arc_drop * (sin_th ** 2)
            else:
                y_contour = cur_b * sin_th * (1.0 - 0.03 * abs(sin_th))
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
            bm.faces.new([r1[i], r1[i_next], r2[i_next], r2[i]])

    # 2. UPPER TORSO:
    # Front panel has columns 2 to 14.
    # Back panel has columns 18 to 30.
    # At top ring (r_up = N_UPPER):
    # Front:
    #   col 2..6: Right shoulder seam (X: shoulder_half_w -> neck_half_w)
    #   col 6..10: Front round neckline (X: neck_half_w -> 0 -> -neck_half_w)
    #   col 10..14: Left shoulder seam (X: -neck_half_w -> -shoulder_half_w)
    # Back:
    #   col 18..22: Left shoulder seam back (X: -shoulder_half_w -> -neck_half_w)
    #   col 22..26: Back round neckline (X: -neck_half_w -> 0 -> neck_half_w)
    #   col 26..30: Right shoulder seam back (X: neck_half_w -> shoulder_half_w)

    # Let's pre-calculate the EXACT target coordinates of the top ring (r_up = N_UPPER)
    # so that the shoulder slope is 100% straight and anatomical, with ZERO humps!
    top_target_coords = [None] * N_PERIM

    # FRONT PANEL TOP (col 2 to 14):
    for i in range(2, 15):
        if i <= 6:
            # Right shoulder seam: i from 2 to 6
            # u_sh: 1.0 at i=2 (shoulder tip), 0.0 at i=6 (HPS)
            u_sh = (6 - i) / 4.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            y = 0.005 * u_sh  # seam line sits at Y ~ 0.005
            z = z_hps - slope_drop * u_sh
        elif i >= 10:
            # Left shoulder seam: i from 10 to 14
            # u_sh: 0.0 at i=10 (HPS), 1.0 at i=14 (shoulder tip)
            u_sh = (i - 10) / 4.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            y = 0.005 * u_sh
            z = z_hps - slope_drop * u_sh
        else:
            # Front round neckline: i from 6 to 10
            # u_neck goes from 0 (at i=6, right HPS) to 1 (at i=8, center front) to 0 (at i=10, left HPS)
            # Angle around front neck: alpha goes from 0 (right HPS) to pi (left HPS)
            alpha = (i - 6) / 4.0 * math.pi
            x = neck_half_w * math.cos(alpha)
            y = neck_front_depth_y * math.sin(alpha)
            z = z_hps - neck_front_drop * (math.sin(alpha) ** 1.3)
        top_target_coords[i] = (x, y, z)

    # BACK PANEL TOP (col 18 to 30):
    for i in range(18, 31):
        if i <= 22:
            # Left shoulder seam back: i from 18 to 22
            # u_sh: 1.0 at i=18 (shoulder tip), 0.0 at i=22 (HPS)
            u_sh = (22 - i) / 4.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            y = 0.005 * u_sh
            z = z_hps - slope_drop * u_sh
        elif i >= 26:
            # Right shoulder seam back: i from 26 to 30
            # u_sh: 0.0 at i=26 (HPS), 1.0 at i=30 (shoulder tip)
            u_sh = (i - 26) / 4.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            y = 0.005 * u_sh
            z = z_hps - slope_drop * u_sh
        else:
            # Back round neckline: i from 22 to 26
            # alpha goes from pi (left HPS) to 0 (right HPS)
            alpha = (26 - i) / 4.0 * math.pi
            x = -neck_half_w * math.cos(alpha)
            y = -neck_back_depth_y * math.sin(alpha)
            z = z_hps - neck_back_drop * (math.sin(alpha) ** 1.3)
        top_target_coords[i] = (x, y, z)

    # Fill intermediate upper rings by smoothly interpolating from underarm ring to top_target_coords!
    underarm_ring = torso_rings[N_LOWER]

    for r_up in range(1, N_UPPER + 1):
        t_up = r_up / float(N_UPPER)
        t_ease = t_up * t_up * (3.0 - 2.0 * t_up)

        ring = []
        for i in range(N_PERIM):
            if top_target_coords[i] is not None:
                # Interpolate smoothly from underarm ring to top target
                v_under = underarm_ring[i]
                tx, ty, tz = top_target_coords[i]

                # Scye armhole indent in intermediate rings
                scye_in = 0.020 * math.sin(math.pi * t_up)
                if abs(tx) > neck_half_w:
                    side_sign = 1.0 if tx > 0 else -1.0
                    x_interp = v_under.co.x * (1 - t_ease) + tx * t_ease - side_sign * scye_in
                else:
                    x_interp = v_under.co.x * (1 - t_ease) + tx * t_ease

                y_interp = v_under.co.y * (1 - t_ease) + ty * t_ease
                z_interp = v_under.co.z * (1 - t_ease) + tz * t_ease

                v = bm.verts.new((x_interp, y_interp, z_interp))
            else:
                # Unused lateral underarm columns (0, 1, 15, 16, 17, 31)
                # Just keep smooth dummy position for indexing
                v = bm.verts.new((0, 0, z_underarm))
            ring.append(v)
        torso_rings.append(ring)

    # Stitch upper torso panels
    for r in range(N_LOWER, N_LOWER + N_UPPER):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]

        # Front panel quads: col 2 to 14
        for i in range(2, 14):
            bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])

        # Back panel quads: col 18 to 30
        for i in range(18, 30):
            bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])

    # 3. SHOULDER SEAMS:
    # Right shoulder: connect front col 2..6 to back col 30..26!
    # Exactly 4 quads along the shoulder seam!
    top_ring = torso_rings[-1]
    for k in range(4):
        # Front: 2+k to 3+k
        # Back: 30-k to 29-k
        f1 = top_ring[2 + k]
        f2 = top_ring[3 + k]
        b1 = top_ring[30 - k]
        b2 = top_ring[29 - k]
        bm.faces.new([f1, f2, b2, b1])

    # Left shoulder: connect front col 10..14 to back col 22..18!
    for k in range(4):
        # Front: 10+k to 11+k
        # Back: 22-k to 21-k
        f1 = top_ring[10 + k]
        f2 = top_ring[11 + k]
        b1 = top_ring[22 - k]
        b2 = top_ring[21 - k]
        bm.faces.new([f1, f2, b2, b1])

    # 4. ROUND NECKLINE & 3D RIBBED COLLAR BAND
    # Boundary loop of the neck opening:
    # Front: 6 -> 7 -> 8 -> 9 -> 10
    # Left HPS seam: (10, 22) is the inner edge of left shoulder seam!
    # Back: 22 -> 23 -> 24 -> 25 -> 26
    # Right HPS seam: (26, 6) is the inner edge of right shoulder seam!
    neck_boundary = [top_ring[i] for i in range(6, 11)] + [top_ring[i] for i in range(22, 27)]
    N_neck = len(neck_boundary)

    # 3D Ribbed collar:
    # Base ring = neck_boundary
    # Top rib ring: extruded inward (-1.8 cm) and standing up (+1.4 cm)
    coll_w = 0.018  # 1.8 cm collar rib width
    coll_h = 0.014  # 1.4 cm collar stand height
    inner_neck = []
    for vn in neck_boundary:
        r_xy = math.hypot(vn.co.x, vn.co.y)
        scale = max(0.5, (r_xy - coll_w) / r_xy)
        v = bm.verts.new((vn.co.x * scale, vn.co.y * scale, vn.co.z + coll_h))
        inner_neck.append(v)

    # Stitch collar rib quads (open boundary inside!)
    for i in range(N_neck):
        i_next = (i + 1) % N_neck
        bm.faces.new([neck_boundary[i], neck_boundary[i_next], inner_neck[i_next], inner_neck[i]])

    # 5. RIGHT & LEFT ARMHOLES AND NATURAL DRAPED SLEEVES
    right_ah = []
    for r in range(N_LOWER + N_UPPER, N_LOWER - 1, -1):
        right_ah.append(torso_rings[r][2])
    right_ah.append(torso_rings[N_LOWER][1])
    right_ah.append(torso_rings[N_LOWER][0])
    right_ah.append(torso_rings[N_LOWER][31])
    for r in range(N_LOWER, N_LOWER + N_UPPER + 1):
        right_ah.append(torso_rings[r][30])

    left_ah = []
    for r in range(N_LOWER + N_UPPER, N_LOWER - 1, -1):
        left_ah.append(torso_rings[r][14])
    left_ah.append(torso_rings[N_LOWER][15])
    left_ah.append(torso_rings[N_LOWER][16])
    left_ah.append(torso_rings[N_LOWER][17])
    for r in range(N_LOWER, N_LOWER + N_UPPER + 1):
        left_ah.append(torso_rings[r][18])

    sleeve_rings_count = 11
    drape_deg = 50.0
    drape_rad = math.radians(drape_deg)
    fwd_deg = 3.5
    fwd_rad = math.radians(fwd_deg)

    a_cuff, b_cuff = solve_ellipse_radii(sleeve_opening, 1.14)

    def loft_seamless_sleeve(ah_loop, side_sign):
        N_pts = len(ah_loop)
        cx_ah = sum(v.co.x for v in ah_loop) / N_pts
        cy_ah = sum(v.co.y for v in ah_loop) / N_pts
        cz_ah = sum(v.co.z for v in ah_loop) / N_pts
        C_ah = np.array([cx_ah, cy_ah, cz_ah])

        # Sleeve unit direction vector
        w_dir = np.array([
            math.cos(drape_rad) * side_sign,
            math.sin(fwd_rad),
            -math.sin(drape_rad)
        ])
        w_unit = w_dir / np.linalg.norm(w_dir)

        # In-plane transverse axis
        u1 = np.array([
            math.sin(drape_rad) * side_sign,
            0.0,
            math.cos(drape_rad)
        ])
        u1 = u1 / np.linalg.norm(u1)

        # Sagittal axis
        u2 = np.cross(w_unit, u1)
        u2 = u2 / np.linalg.norm(u2)

        ah_coords = []
        for v in ah_loop:
            rel = np.array([v.co.x, v.co.y, v.co.z]) - C_ah
            p1 = np.dot(rel, u1)
            p2 = np.dot(rel, u2)
            phi = math.atan2(p2, p1)
            ah_coords.append((p1, p2, phi))

        prev_ring = ah_loop

        for r_idx in range(1, sleeve_rings_count + 1):
            t = r_idx / float(sleeve_rings_count)
            t_ease = t * t * (3.0 - 2.0 * t)

            # Curved drape trajectory with gravity sag
            gravity_sag = 0.010 * (t ** 1.8)

            cur_ring = []
            for i in range(N_pts):
                p1_base, p2_base, phi = ah_coords[i]

                # Tailored length progression along arm axis:
                # Top of sleeve cap (phi ~ pi/2) curves naturally over shoulder endpoint
                # Underarm seam (phi ~ -pi/2) is shorter to prevent bunching
                cap_weight = math.sin(phi)
                ring_disp = (sleeve * t) * (1.0 + 0.08 * cap_weight * (1.0 - t_ease))

                # Target planar elliptical cuff profile
                q1_target = a_cuff * math.cos(phi)
                q2_target = b_cuff * math.sin(phi)

                # Smooth blend from armhole loop to elliptical cuff
                c1 = p1_base * (1.0 - t_ease) + q1_target * t_ease
                c2 = p2_base * (1.0 - t_ease) + q2_target * t_ease

                # NOTE: NO artificial "+= deltoid bump" that creates shoulder humps!
                # The sleeve smoothly follows the armhole boundary and shoulder line!

                V_3d = C_ah + ring_disp * w_unit + np.array([0.0, 0.0, -gravity_sag]) + c1 * u1 + c2 * u2
                v_new = bm.verts.new(tuple(V_3d))
                cur_ring.append(v_new)

            for i in range(N_pts):
                i_next = (i + 1) % N_pts
                if side_sign > 0:
                    bm.faces.new([prev_ring[i], prev_ring[i_next], cur_ring[i_next], cur_ring[i]])
                else:
                    bm.faces.new([prev_ring[i_next], prev_ring[i], cur_ring[i], cur_ring[i_next]])
            prev_ring = cur_ring

    loft_seamless_sleeve(right_ah, +1.0)
    loft_seamless_sleeve(left_ah, -1.0)

    # 6. MESH VALIDATION & MODIFIERS
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    non_manifold = [e for e in bm.edges if not e.is_manifold and not e.is_boundary]
    print(f"Non-manifold internal edges count: {len(non_manifold)}")
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    print(f"Open boundary edges count: {len(boundary_edges)} (Expected: hem 32 + neck 10 + left cuff 21 + right cuff 21 = 84)")

    mesh = bpy.data.meshes.new(f"ParametricTshirt_{selected_size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(f"Garment_{selected_size}", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Subdivision surface for smooth cloth representation
    subsurf = obj.modifiers.new(name="SubdivisionSurface", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Neutral studio material
    mat = bpy.data.materials.new(name="StudioGarmentMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.86, 0.86, 0.88, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.78
    obj.data.materials.append(mat)

    bpy.context.view_layer.update()
    dims = obj.dimensions
    vert_count = len(mesh.vertices)
    face_count = len(mesh.polygons)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_normals=True
    )
    print(f"Exported to {output_path}. Dims: X={dims.x:.3f}, Y={dims.y:.3f}, Z={dims.z:.3f}")
    print(f"Vertices: {vert_count}, Faces: {face_count}")

if __name__ == "__main__":
    cfg = {
        "garment_type": "regular_tshirt",
        "selected_size": "S",
        "fit": "regular",
        "sleeve_type": "short",
        "neck_type": "round",
        "measurements": {
            "chest": 0.96,
            "shoulder": 0.40,
            "length": 0.66,
            "sleeve": 0.18
        }
    }
    build_perfect_tshirt(cfg, "storage/generated_models/test_perfect_s.glb")
