"""Prototype of the improved realistic parametric 3D T-shirt generator."""
import sys
import os
import math
import json

try:
    import bpy
    import bmesh
except ImportError:
    print("Run via Blender: blender -b -P scripts/test_improved_garment.py")
    sys.exit(1)

def solve_ellipse_radii(circ: float, aspect: float = 1.55):
    """Accurate Ramanujan ellipse circumference solver."""
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

def build_realistic_tshirt(config: dict, output_glb_path: str):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    measurements = config.get("measurements", {})
    chest = float(measurements.get("chest", 1.07))
    shoulder = float(measurements.get("shoulder", 0.46))
    length = float(measurements.get("length", 0.71))
    sleeve = float(measurements.get("sleeve", 0.20))
    fit = config.get("fit", "regular")
    neck_type = config.get("neck_type", "round")
    selected_size = config.get("selected_size", "L")

    # Fit-specific adjustments
    if fit == "slim":
        waist_circ = chest * 0.92
        hem_circ = chest * 0.95
        aspect = 1.52
    elif fit == "relaxed":
        waist_circ = chest * 1.00
        hem_circ = chest * 1.02
        aspect = 1.60
    else:  # regular
        waist_circ = chest * 0.96
        hem_circ = chest * 0.98
        aspect = 1.56

    waist_circ = float(measurements.get("waist") or waist_circ)
    hem_circ = float(measurements.get("hem") or hem_circ)
    sleeve_opening = float(measurements.get("sleeve_opening") or (chest * 0.34))

    # Radii along height
    a_hem, b_hem = solve_ellipse_radii(hem_circ, aspect * 0.98)
    a_waist, b_waist = solve_ellipse_radii(waist_circ, aspect)
    a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.02)

    # Vertical landmarks
    z_hem = 0.0
    z_waist = length * 0.42
    # Armhole depth: standard tailoring is ~ 45-48% of shoulder width, typically 21-24cm for Size L
    armhole_depth = max(0.20, shoulder * 0.48)
    z_underarm = length - armhole_depth

    # Shoulder and Neckline landmarks
    shoulder_half_w = shoulder / 2.0
    neck_half_w = shoulder * 0.21  # neck width ~ 19-20 cm
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(14.0)) # ~14 deg slope
    z_hps = length # High Point Shoulder
    z_shoulder_tip = z_hps - slope_drop

    neck_front_drop = 0.12 if neck_type == "v_neck" else 0.088
    neck_back_drop = 0.026

    bm = bmesh.new()

    # -------------------------------------------------------------
    # 1. TORSO SURFACE: Structured Continuous Quad Grid
    # We build the torso as cross-sectional rings from Hem to Shoulder!
    # Ring resolution: N_points = 32 around the perimeter.
    # From Z=0 to Z=z_underarm: 10 closed rings.
    # From Z=z_underarm to Z=z_hps: 6 rings that separate into Front panel,
    # Back panel, and Armhole cutouts, ending at the Neckline & Shoulder seams!
    # -------------------------------------------------------------
    N_PERIM = 32 # Must be multiple of 4
    # Points 0..N_PERIM-1:
    # 0: Right side seam (+X)
    # N/4 (8): Front center (+Y)
    # N/2 (16): Left side seam (-X)
    # 3N/4 (24): Back center (-Y)

    # LOWER TORSO (Z = 0 to Z = z_underarm)
    N_LOWER_RINGS = 10
    lower_rings = []

    for r in range(N_LOWER_RINGS + 1):
        t = r / float(N_LOWER_RINGS)
        z = z_hem + t * z_underarm

        # Smooth spline interpolation between hem, waist, and chest
        if t < 0.45:
            s = t / 0.45
            # Cosine ease
            s = 0.5 * (1.0 - math.cos(math.pi * s))
            a = a_hem * (1 - s) + a_waist * s
            b = b_hem * (1 - s) + b_waist * s
        else:
            s = (t - 0.45) / 0.55
            s = 0.5 * (1.0 - math.cos(math.pi * s))
            a = a_waist * (1 - s) + a_chest * s
            b = b_waist * (1 - s) + b_chest * s

        ring_verts = []
        for i in range(N_PERIM):
            theta = 2.0 * math.pi * i / N_PERIM
            # Anatomical chest shape: front (+Y, sin > 0) has gentle pectoral convexity,
            # back (-Y, sin < 0) has smooth scapular flatter contour
            sin_th = math.sin(theta)
            cos_th = math.cos(theta)

            if sin_th > 0:
                y_contour = b * sin_th * (1.0 + 0.06 * math.sin(theta)) + 0.006 * sin_th
            else:
                y_contour = b * sin_th * (1.0 - 0.03 * math.sin(theta))

            x_contour = a * cos_th

            v = bm.verts.new((x_contour, y_contour, z))
            ring_verts.append(v)
        lower_rings.append(ring_verts)

    # Stitch lower torso quad rings
    for r in range(N_LOWER_RINGS):
        r_curr = lower_rings[r]
        r_next = lower_rings[r + 1]
        for i in range(N_PERIM):
            i_next = (i + 1) % N_PERIM
            bm.faces.new([r_curr[i], r_curr[i_next], r_next[i_next], r_next[i]])

    # -------------------------------------------------------------
    # 2. UPPER TORSO: Front & Back Panels with Anatomical Scye (Armhole)
    # The underarm ring (top of lower torso) is lower_rings[-1].
    # Indices:
    # Right armhole cutout spans indices [30, 31, 0, 1, 2]
    # Front chest panel spans indices [2 .. 14]
    # Left armhole cutout spans indices [14, 15, 16, 17, 18]
    # Back chest panel spans indices [18 .. 30]
    # -------------------------------------------------------------
    N_UPPER_LAYERS = 6
    # We build rows of vertices for Front Panel and Back Panel
    # Front panel has 11 columns (from col 2 to 14)
    # Back panel has 11 columns (from col 18 to 30)
    front_grid = [lower_rings[-1][2:15]] # layer 0 (13 vertices: index 2 to 14)
    back_grid = [lower_rings[-1][18:31]] # layer 0 (13 vertices: index 18 to 30)

    for lyr in range(1, N_UPPER_LAYERS + 1):
        t = lyr / float(N_UPPER_LAYERS)
        z_nominal = z_underarm + t * (z_shoulder_tip - z_underarm)

        front_layer = []
        back_layer = []

        # Lateral armhole indentation (scye curve)
        # Deepest indentation is at mid-armhole (t ~ 0.4 - 0.6)
        scye_indent = 0.028 * math.sin(math.pi * t)

        for col_idx in range(13):
            # u runs from -1.0 (right side) to +1.0 (left side)
            u = 1.0 - 2.0 * (col_idx / 12.0) # +1 at col 0, -1 at col 12

            # X position smoothly bridges from underarm width to shoulder width
            current_half_w = a_chest * (1 - t) + shoulder_half_w * t - scye_indent * (1 - abs(u) * 0.4)
            vx = current_half_w * u

            # Y depth at this height
            depth_factor = 1.0 - 0.15 * t
            vy_front = b_chest * depth_factor * math.sqrt(max(0.001, 1.0 - (u * 0.85)**2)) * 0.88 + 0.008
            vy_back = -b_chest * depth_factor * math.sqrt(max(0.001, 1.0 - (u * 0.85)**2)) * 0.82

            # Z contour: shoulders slope downward from neck to shoulder tip,
            # and neckline scoops downward in the center (u ~ 0)
            center_factor = math.cos(math.pi * 0.5 * min(1.0, abs(u) / 0.55))

            if lyr == N_UPPER_LAYERS:
                # Top edge: collar and shoulder seam
                # Neck opening width is neck_half_w
                is_neck_zone = abs(vx) < neck_half_w
                if is_neck_zone:
                    # Scoop down for neck
                    neck_t = 1.0 - (abs(vx) / neck_half_w)**2
                    vz_front = z_hps - neck_front_drop * neck_t
                    vz_back = z_hps - neck_back_drop * neck_t
                else:
                    # Shoulder slope
                    sh_t = (abs(vx) - neck_half_w) / max(0.001, shoulder_half_w - neck_half_w)
                    vz = z_hps - slope_drop * sh_t
                    vz_front = vz
                    vz_back = vz
            else:
                # Intermediate layers have smooth subtle neck-pre-scoop
                vz_front = z_nominal - 0.03 * (t**2) * (1.0 - (u)**2)
                vz_back = z_nominal - 0.01 * (t**2) * (1.0 - (u)**2)

            vf = bm.verts.new((vx, vy_front, vz_front))
            vb = bm.verts.new((vx, vy_back, vz_back))
            front_layer.append(vf)
            back_layer.append(vb)

        front_grid.append(front_layer)
        back_grid.append(back_layer)

    # Stitch front grid quads
    for lyr in range(N_UPPER_LAYERS):
        r1 = front_grid[lyr]
        r2 = front_grid[lyr + 1]
        for c in range(12):
            bm.faces.new([r1[c], r1[c + 1], r2[c + 1], r2[c]])

    # Stitch back grid quads
    for lyr in range(N_UPPER_LAYERS):
        r1 = back_grid[lyr]
        r2 = back_grid[lyr + 1]
        for c in range(12):
            bm.faces.new([r1[c + 1], r1[c], r2[c], r2[c + 1]])

    # Connect shoulder seams (top of front grid to top of back grid outside neck)
    # col 0..3 are right shoulder, col 9..12 are left shoulder
    top_f = front_grid[-1]
    top_b = back_grid[-1]
    for c in range(3):
        bm.faces.new([top_f[c], top_f[c + 1], top_b[c + 1], top_b[c]])
    for c in range(9, 12):
        bm.faces.new([top_f[c], top_f[c + 1], top_b[c + 1], top_b[c]])

    # -------------------------------------------------------------
    # 3. CREW-NECK COLLAR RIB
    # Formed by the top front neck loop (indices 3..9) and back neck loop (indices 3..9)
    # Extrude an authentic 2.2cm collar band with realistic dual-wall rib
    # -------------------------------------------------------------
    collar_front_pts = top_f[3:10] # 7 vertices
    collar_back_pts = top_b[3:10]  # 7 vertices

    # Collar rim inner vertices
    coll_rib_w = 0.022 # 2.2 cm collar width
    inner_front = []
    inner_back = []
    for vf in collar_front_pts:
        # Vector towards neck center
        dx = -vf.co.x * 0.15
        dy = -vf.co.y * 0.18
        v = bm.verts.new((vf.co.x + dx, vf.co.y + dy, vf.co.z - coll_rib_w * 0.6))
        inner_front.append(v)
    for vb in collar_back_pts:
        dx = -vb.co.x * 0.15
        dy = -vb.co.y * 0.18
        v = bm.verts.new((vb.co.x + dx, vb.co.y + dy, vb.co.z - coll_rib_w * 0.6))
        inner_back.append(v)

    # Stitch collar rib quads
    for c in range(6):
        bm.faces.new([collar_front_pts[c], collar_front_pts[c + 1], inner_front[c + 1], inner_front[c]])
        bm.faces.new([collar_back_pts[c + 1], collar_back_pts[c], inner_back[c], inner_back[c + 1]])
    # Close collar sides at shoulder junctions
    bm.faces.new([collar_front_pts[0], inner_front[0], inner_back[0], collar_back_pts[0]])
    bm.faces.new([collar_front_pts[-1], collar_back_pts[-1], inner_back[-1], inner_front[-1]])

    # -------------------------------------------------------------
    # 4. ANATOMICAL ARMHOLES & REALISTIC DRAPED SLEEVES
    # Now that upper torso is an organic quad grid, each armhole perimeter
    # is a completely continuous sequence of 14 vertices!
    # Right armhole loop:
    # Along Front panel right edge (col 0): front_grid[lyr][0] from lyr=0 to N_UPPER_LAYERS
    # Across shoulder seam: top_f[0] -> top_b[0]
    # Along Back panel right edge (col 0): back_grid[lyr][0] from lyr=N_UPPER_LAYERS down to 0
    # Across underarm: underarm connection in lower_rings[-1]
    # -------------------------------------------------------------
    # Right underarm filling: lower_rings[-1] points 31, 0, 1
    v_ua_r = lower_rings[-1][0]
    v_ua_f_r = lower_rings[-1][1]
    v_ua_b_r = lower_rings[-1][31]

    # Stitch underarm gusset
    bm.faces.new([front_grid[0][0], v_ua_f_r, v_ua_r])
    bm.faces.new([back_grid[0][0], v_ua_r, v_ua_b_r])

    right_armhole = []
    # 1. Shoulder tip (top)
    right_armhole.append(top_f[0])
    # 2. Front scye curve (descending from top_f[0] down to front_grid[0][0])
    for lyr in range(N_UPPER_LAYERS - 1, -1, -1):
        right_armhole.append(front_grid[lyr][0])
    # 3. Underarm bottom
    right_armhole.append(v_ua_r)
    # 4. Back scye curve (ascending from back_grid[0][0] up to top_b[0])
    for lyr in range(0, N_UPPER_LAYERS):
        right_armhole.append(back_grid[lyr][0])

    # Left underarm filling: lower_rings[-1] points 15, 16, 17
    v_ua_l = lower_rings[-1][16]
    v_ua_f_l = lower_rings[-1][15]
    v_ua_b_l = lower_rings[-1][17]

    bm.faces.new([front_grid[0][-1], v_ua_r if False else v_ua_l, v_ua_f_l])
    bm.faces.new([back_grid[0][-1], v_ua_b_l, v_ua_l])

    left_armhole = []
    left_armhole.append(top_f[-1])
    for lyr in range(N_UPPER_LAYERS - 1, -1, -1):
        left_armhole.append(front_grid[lyr][-1])
    left_armhole.append(v_ua_l)
    for lyr in range(0, N_UPPER_LAYERS):
        left_armhole.append(back_grid[lyr][-1])

    # Now loft sleeves from these clean 14-vertex armhole loops!
    sleeve_rings_count = 8
    # Realistic relaxed T-shirt sleeve angle: 52 degrees downward from horizontal,
    # 4 degrees forward.
    drape_rad = math.radians(52.0)
    cos_d = math.cos(drape_rad)
    sin_d = math.sin(drape_rad)
    fwd_rad = math.radians(4.0)

    # Cuff radii
    a_cuff, b_cuff = solve_ellipse_radii(sleeve_opening, 1.18)

    def generate_sleeve_mesh(armhole_verts, side_sign):
        N_pts = len(armhole_verts)
        # Compute centroid of armhole
        cx_ah = sum(v.co.x for v in armhole_verts) / N_pts
        cy_ah = sum(v.co.y for v in armhole_verts) / N_pts
        cz_ah = sum(v.co.z for v in armhole_verts) / N_pts

        # Cuff center
        cuff_cx = cx_ah + sleeve * cos_d * side_sign
        cuff_cy = cy_ah + sleeve * math.sin(fwd_rad)
        cuff_cz = cz_ah - sleeve * sin_d

        prev_ring = armhole_verts

        for r_idx in range(1, sleeve_rings_count + 1):
            t = r_idx / float(sleeve_rings_count)
            # Smooth ease along sleeve
            t_ease = t * t * (3.0 - 2.0 * t)

            # Center of current ring
            rcx = cx_ah * (1 - t) + cuff_cx * t
            rcy = cy_ah * (1 - t) + cuff_cy * t
            rcz = cz_ah * (1 - t) + cuff_cz * t

            # Radii at current ring
            cur_a = a_cuff * t_ease + (armhole_depth * 0.42) * (1 - t_ease)
            cur_b = b_cuff * t_ease + (armhole_depth * 0.38) * (1 - t_ease)

            cur_ring = []
            for i, base_v in enumerate(armhole_verts):
                # Parametric angle around the loop
                phi = 2.0 * math.pi * i / N_pts

                # Vector perpendicular to sleeve centerline
                # Lateral offset in cross section:
                # u1 = (sin_d * side_sign, 0, cos_d)
                # u2 = (0, 1, 0)
                dx = cur_a * math.cos(phi) * sin_d * side_sign
                dy = cur_b * math.sin(phi)
                dz = -cur_a * math.cos(phi) * cos_d

                # Natural deltoid convexity on upper sleeve cap (t < 0.4)
                if i < 3 or i > N_pts - 4:
                    deltoid_bump = 0.015 * math.sin(math.pi * min(1.0, t / 0.5))
                    dz += deltoid_bump

                target_x = rcx + dx
                target_y = rcy + dy
                target_z = rcz + dz

                # Blend smoothly from base armhole vertex coordinates to idealized tube
                vx = base_v.co.x * (1 - t_ease) + target_x * t_ease
                vy = base_v.co.y * (1 - t_ease) + target_y * t_ease
                vz = base_v.co.z * (1 - t_ease) + target_z * t_ease

                v = bm.verts.new((vx, vy, vz))
                cur_ring.append(v)

            # Connect quad strip
            for i in range(N_pts):
                i_next = (i + 1) % N_pts
                if side_sign > 0:
                    bm.faces.new([prev_ring[i], prev_ring[i_next], cur_ring[i_next], cur_ring[i]])
                else:
                    bm.faces.new([prev_ring[i_next], prev_ring[i], cur_ring[i], cur_ring[i_next]])
            prev_ring = cur_ring

    generate_sleeve_mesh(right_armhole, +1.0)
    generate_sleeve_mesh(left_armhole, -1.0)

    # Clean up and normalize
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

    # 5. Modifiers for Realism:
    # A. Subdivision Surface modifier: turns structured quad grid into silky organic cloth!
    subsurf = obj.modifiers.new(name="SubdivisionSurface", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    # B. Solidify modifier: realistic 1.6mm fabric thickness
    solid = obj.modifiers.new(name="FabricThickness", type='SOLIDIFY')
    solid.thickness = 0.0016
    solid.offset = 0.0
    solid.use_rim = True

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    # PBR Cotton Material
    mat = bpy.data.materials.new(name="StudioGarmentMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.86, 0.86, 0.88, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.78
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

    metadata = {
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.polygons),
        "dimensions": {
            "width_m": round(dims.x, 4),
            "height_m": round(dims.z, 4),
            "depth_m": round(dims.y, 4)
        }
    }
    print("GENERATION_METADATA:" + json.dumps(metadata))
    print(f"Successfully generated improved model to {output_glb_path}")

if __name__ == "__main__":
    test_cfg = {
        "garment_type": "regular_tshirt",
        "selected_size": "L",
        "fit": "regular",
        "sleeve_type": "short",
        "neck_type": "round",
        "measurements": {
            "chest": 1.07,
            "shoulder": 0.46,
            "length": 0.71,
            "sleeve": 0.20
        }
    }
    build_realistic_tshirt(test_cfg, "storage/generated_models/test_improved_tshirt.glb")
