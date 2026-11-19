"""Test comprehensive parametric geometry improvements specifically verified for Size S."""
import os
import sys
import math
import json
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

def build_natural_tshirt(config: dict, output_path: str):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    measurements = config.get("measurements", {})
    chest = float(measurements.get("chest", 0.96))
    shoulder = float(measurements.get("shoulder", 0.40))
    length = float(measurements.get("length", 0.66))
    sleeve = float(measurements.get("sleeve", 0.18))
    fit = config.get("fit", "regular")
    neck_type = config.get("neck_type", "round")
    selected_size = config.get("selected_size", "S")

    # Regular fit sizing ratios
    aspect = 1.54
    waist_circ = float(measurements.get("waist") or (chest * 0.95))
    hem_circ = float(measurements.get("hem") or (chest * 0.98))
    sleeve_opening = float(measurements.get("sleeve_opening") or (chest * 0.33))

    a_hem, b_hem = solve_ellipse_radii(hem_circ, aspect * 0.97)
    a_waist, b_waist = solve_ellipse_radii(waist_circ, aspect)
    a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.02)

    z_hem = 0.0
    z_waist = length * 0.40
    armhole_depth = max(0.185, shoulder * 0.48)
    z_underarm = length - armhole_depth

    shoulder_half_w = shoulder / 2.0
    neck_half_w = shoulder * 0.22
    # 14.0 degree anatomical shoulder slope
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(14.0))
    z_hps = length
    z_shoulder_tip = z_hps - slope_drop

    neck_front_drop = 0.115 if neck_type == "v_neck" else 0.082
    neck_back_drop = 0.024

    bm = bmesh.new()

    # Resolution
    N_PERIM = 32
    N_LOWER = 11  # 11 rings between hem and underarm
    N_UPPER = 8   # 8 rings between underarm and shoulder
    N_TOTAL = N_LOWER + N_UPPER

    torso_rings = []

    # -------------------------------------------------------------------------
    # 1. TORSO GENERATION WITH NATURAL SURFACE & WAIST CONTOURS
    # -------------------------------------------------------------------------
    for r in range(N_TOTAL + 1):
        if r <= N_LOWER:
            t = r / float(N_LOWER)
            # Smooth S-curve spline from hem to waist to chest
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

            # Subtle natural hem arc: side seams are 1.0cm higher than center front/back
            hem_arc_drop = 0.010 * (1.0 - t)**1.8
            z_nominal = z_hem + t * z_underarm

            ring = []
            for i in range(N_PERIM):
                theta = 2.0 * math.pi * i / N_PERIM
                sin_th = math.sin(theta)
                cos_th = math.cos(theta)

                # Organic chest curvature: smooth pectoral volume anteriorly
                if sin_th > 0:
                    y_contour = cur_b * sin_th * (1.0 + 0.06 * sin_th - 0.015 * math.sin(3.0 * theta)) + 0.005 * sin_th
                    vz = z_nominal - hem_arc_drop * (sin_th**2)
                else:
                    y_contour = cur_b * sin_th * (1.0 - 0.03 * abs(sin_th))
                    vz = z_nominal - hem_arc_drop * 0.7 * (sin_th**2)

                x_contour = cur_a * cos_th
                v = bm.verts.new((x_contour, y_contour, vz))
                ring.append(v)
            torso_rings.append(ring)

        else:
            t_up = (r - N_LOWER) / float(N_UPPER)
            z_nominal = z_underarm + t_up * (z_shoulder_tip - z_underarm)

            # Natural tailored armhole scye indent (curves inward then flares to shoulder tip)
            scye_indent = 0.024 * math.sin(math.pi * t_up)
            cur_half_w = a_chest * (1 - t_up) + shoulder_half_w * t_up - scye_indent
            cur_b = b_chest * (1.0 - 0.16 * t_up)

            ring = []
            for i in range(N_PERIM):
                theta = 2.0 * math.pi * i / N_PERIM
                sin_th = math.sin(theta)
                cos_th = math.cos(theta)

                x_contour = cur_half_w * cos_th
                if sin_th > 0:
                    y_contour = cur_b * sin_th * (1.0 + 0.05 * sin_th) + 0.005 * sin_th
                else:
                    y_contour = cur_b * sin_th * (1.0 - 0.02 * abs(sin_th))

                vz = z_nominal
                if r == N_TOTAL:
                    # Top ring: shoulder slope and neckline dips
                    if abs(x_contour) < neck_half_w:
                        neck_t = 1.0 - (abs(x_contour) / neck_half_w) ** 1.6
                        if sin_th > 0:
                            vz = z_hps - neck_front_drop * neck_t
                        else:
                            vz = z_hps - neck_back_drop * neck_t
                    else:
                        sh_t = (abs(x_contour) - neck_half_w) / max(0.001, shoulder_half_w - neck_half_w)
                        vz = z_hps - slope_drop * sh_t
                else:
                    # Natural pectoral lift towards chest
                    if sin_th > 0:
                        vz = z_nominal - 0.018 * (t_up ** 2) * (sin_th ** 2)
                    else:
                        vz = z_nominal - 0.008 * (t_up ** 2) * (sin_th ** 2)

                v = bm.verts.new((x_contour, y_contour, vz))
                ring.append(v)
            torso_rings.append(ring)

    # 1. Stitch lower torso rings (continuous quads)
    for r in range(N_LOWER):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]
        for i in range(N_PERIM):
            i_next = (i + 1) % N_PERIM
            bm.faces.new([r1[i], r1[i_next], r2[i_next], r2[i]])

    # 2. Stitch upper torso front and back panels
    for r in range(N_LOWER, N_TOTAL):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]
        # Front panel quads: col 2 to 14
        for i in range(2, 14):
            bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
        # Back panel quads: col 18 to 30
        for i in range(18, 30):
            bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])

    # 3. Stitch top shoulder seams outside neck opening
    top_ring = torso_rings[-1]
    # Right shoulder: connect front [2, 3, 4] to back [30, 29, 28]
    bm.faces.new([top_ring[2], top_ring[3], top_ring[29], top_ring[30]])
    bm.faces.new([top_ring[3], top_ring[4], top_ring[28], top_ring[29]])

    # Left shoulder: connect front [12, 13, 14] to back [20, 19, 18]
    bm.faces.new([top_ring[12], top_ring[13], top_ring[19], top_ring[20]])
    bm.faces.new([top_ring[13], top_ring[14], top_ring[18], top_ring[19]])

    # -------------------------------------------------------------------------
    # 2. COLLAR RIB BAND (Open boundary loop for neck entry)
    # -------------------------------------------------------------------------
    neck_cycle = [top_ring[i] for i in range(4, 13)] + [top_ring[i] for i in range(20, 29)]
    N_neck = len(neck_cycle)

    coll_w = 0.022  # 2.2 cm collar rib width
    inner_neck = []
    for vn in neck_cycle:
        r_xy = math.hypot(vn.co.x, vn.co.y)
        scale = max(0.5, (r_xy - coll_w) / r_xy)
        # Stand up slightly (+2.5mm) for realistic ribbed collar thickness and profile
        v = bm.verts.new((vn.co.x * scale, vn.co.y * scale, vn.co.z + 0.003))
        inner_neck.append(v)

    for i in range(N_neck):
        i_next = (i + 1) % N_neck
        bm.faces.new([neck_cycle[i], neck_cycle[i_next], inner_neck[i_next], inner_neck[i]])

    # -------------------------------------------------------------------------
    # 3. ANATOMICAL SLEEVE LOFTING WITH CURVED DRAPE & DELTOID CAP
    # -------------------------------------------------------------------------
    right_ah = []
    for r in range(N_TOTAL, N_LOWER - 1, -1):
        right_ah.append(torso_rings[r][2])
    right_ah.append(torso_rings[N_LOWER][1])
    right_ah.append(torso_rings[N_LOWER][0])
    right_ah.append(torso_rings[N_LOWER][31])
    for r in range(N_LOWER, N_TOTAL + 1):
        right_ah.append(torso_rings[r][30])

    left_ah = []
    for r in range(N_TOTAL, N_LOWER - 1, -1):
        left_ah.append(torso_rings[r][14])
    left_ah.append(torso_rings[N_LOWER][15])
    left_ah.append(torso_rings[N_LOWER][16])
    left_ah.append(torso_rings[N_LOWER][17])
    for r in range(N_LOWER, N_TOTAL + 1):
        left_ah.append(torso_rings[r][18])

    sleeve_rings_count = 11
    drape_deg = 52.0
    drape_rad = math.radians(drape_deg)
    fwd_deg = 4.0
    fwd_rad = math.radians(fwd_deg)

    a_cuff, b_cuff = solve_ellipse_radii(sleeve_opening, 1.14)

    def loft_realistic_sleeve(ah_loop, side_sign):
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

            # Natural curved drape trajectory (curves down with gravity)
            gravity_sag = 0.012 * (t ** 1.8)
            C_ring = C_ah + (sleeve * t) * w_unit + np.array([0.0, 0.0, -gravity_sag])

            cur_ring = []
            for i in range(N_pts):
                p1_base, p2_base, phi = ah_coords[i]

                # Tailored cap length differential: sleeve cap (top) travels further than underarm
                # phi ~ pi/2 is shoulder cap, phi ~ -pi/2 is underarm
                cap_weight = math.sin(phi)
                # Progressive length displacement along sleeve
                ring_disp = (sleeve * t) * (1.0 + 0.12 * cap_weight * (1.0 - t_ease))
                
                # Target planar elliptical cuff profile
                q1_target = a_cuff * math.cos(phi)
                q2_target = b_cuff * math.sin(phi)

                # Smooth transition from armhole profile to elliptical cuff
                c1 = p1_base * (1.0 - t_ease) + q1_target * t_ease
                c2 = p2_base * (1.0 - t_ease) + q2_target * t_ease

                # Subtle anatomical deltoid curve over top of sleeve cap
                if c1 > 0:
                    deltoid = 0.014 * math.sin(math.pi * min(1.0, t / 0.55)) * (c1 / max(0.01, a_cuff))
                    c1 += deltoid

                # 3D position
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

    loft_realistic_sleeve(right_ah, +1.0)
    loft_realistic_sleeve(left_ah, -1.0)

    # -------------------------------------------------------------------------
    # 4. MESH VALIDATION & TOPOLOGY CHECKS
    # -------------------------------------------------------------------------
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    non_manifold = [e for e in bm.edges if not e.is_manifold and not e.is_boundary]
    print(f"Non-manifold internal edges count: {len(non_manifold)}")

    boundary_edges = [e for e in bm.edges if e.is_boundary]
    print(f"Open boundary edges count: {len(boundary_edges)} (Expected: hem 32 + neck 18 + left cuff 20 + right cuff 20 = 90)")

    # Convert to Blender mesh
    mesh = bpy.data.meshes.new(f"ParametricTshirt_{selected_size}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(f"Garment_{selected_size}", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Subdivision Surface Modifier (clean smooth quad cloth surface)
    subsurf = obj.modifiers.new(name="SubdivisionSurface", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Neutral studio cotton PBR material
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
    build_natural_tshirt(cfg, "storage/generated_models/test_size_s_natural.glb")
