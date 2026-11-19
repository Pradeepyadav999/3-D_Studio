"""Perfect 2-manifold seamless parametric garment generator."""
import sys
import os
import math
import json

try:
    import bpy
    import bmesh
except ImportError:
    print("Run via Blender")
    sys.exit(1)

def solve_ellipse_radii(circ: float, aspect: float = 1.55):
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

def build_seamless_tshirt(config: dict, output_glb_path: str):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    measurements = config.get("measurements", {})
    chest = float(measurements.get("chest", 1.07))
    shoulder = float(measurements.get("shoulder", 0.46))
    length = float(measurements.get("length", 0.71))
    sleeve = float(measurements.get("sleeve", 0.20))
    fit = config.get("fit", "regular")
    neck_type = config.get("neck_type", "round")
    selected_size = config.get("selected_size", "L")

    # Fit parameters
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
    armhole_depth = max(0.195, shoulder * 0.47)
    z_underarm = length - armhole_depth

    shoulder_half_w = shoulder / 2.0
    neck_half_w = shoulder * 0.21
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(13.8))
    z_hps = length
    z_shoulder_tip = z_hps - slope_drop

    neck_front_drop = 0.125 if neck_type == "v_neck" else 0.088
    neck_back_drop = 0.026

    bm = bmesh.new()

    # Resolution
    N_PERIM = 32
    N_LOWER = 10
    N_UPPER = 7
    N_TOTAL = N_LOWER + N_UPPER

    torso_rings = []

    for r in range(N_TOTAL + 1):
        if r <= N_LOWER:
            t = r / float(N_LOWER)
            z_nominal = z_hem + t * z_underarm
            if t < 0.45:
                s = t / 0.45
                s = 0.5 * (1.0 - math.cos(math.pi * s))
                cur_a = a_hem * (1 - s) + a_waist * s
                cur_b = b_hem * (1 - s) + b_waist * s
            else:
                s = (t - 0.45) / 0.55
                s = 0.5 * (1.0 - math.cos(math.pi * s))
                cur_a = a_waist * (1 - s) + a_chest * s
                cur_b = b_waist * (1 - s) + b_chest * s

            ring = []
            for i in range(N_PERIM):
                theta = 2.0 * math.pi * i / N_PERIM
                sin_th = math.sin(theta)
                cos_th = math.cos(theta)

                if sin_th > 0:
                    y_contour = cur_b * sin_th * (1.0 + 0.05 * sin_th) + 0.006 * sin_th
                else:
                    y_contour = cur_b * sin_th * (1.0 - 0.03 * sin_th)

                x_contour = cur_a * cos_th
                v = bm.verts.new((x_contour, y_contour, z_nominal))
                ring.append(v)
            torso_rings.append(ring)

        else:
            t_up = (r - N_LOWER) / float(N_UPPER)
            z_nominal = z_underarm + t_up * (z_shoulder_tip - z_underarm)

            scye_indent = 0.026 * math.sin(math.pi * t_up)
            cur_half_w = a_chest * (1 - t_up) + shoulder_half_w * t_up - scye_indent
            cur_b = b_chest * (1.0 - 0.15 * t_up)

            ring = []
            for i in range(N_PERIM):
                theta = 2.0 * math.pi * i / N_PERIM
                sin_th = math.sin(theta)
                cos_th = math.cos(theta)

                x_contour = cur_half_w * cos_th
                if sin_th > 0:
                    y_contour = cur_b * sin_th * (1.0 + 0.04 * sin_th) + 0.006 * sin_th
                else:
                    y_contour = cur_b * sin_th * (1.0 - 0.02 * sin_th)

                vz = z_nominal
                if r == N_TOTAL:
                    if abs(x_contour) < neck_half_w:
                        neck_t = 1.0 - (abs(x_contour) / neck_half_w)**2
                        if sin_th > 0:
                            vz = z_hps - neck_front_drop * neck_t
                        else:
                            vz = z_hps - neck_back_drop * neck_t
                    else:
                        sh_t = (abs(x_contour) - neck_half_w) / max(0.001, shoulder_half_w - neck_half_w)
                        vz = z_hps - slope_drop * sh_t
                else:
                    if sin_th > 0:
                        vz = z_nominal - 0.025 * (t_up**2) * (sin_th**2)
                    else:
                        vz = z_nominal - 0.010 * (t_up**2) * (sin_th**2)

                v = bm.verts.new((x_contour, y_contour, vz))
                ring.append(v)
            torso_rings.append(ring)

    # 1. Stitch lower torso rings (r: 0 to N_LOWER-1)
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

    # 4. Crew-neck Collar Rib Extrusion (smooth 2-manifold)
    front_collar = [top_ring[i] for i in range(4, 13)] # 9 vertices (col 4 to 12)
    back_collar = [top_ring[i] for i in range(20, 29)] # 9 vertices (col 20 to 28)

    # Form a single closed 16-edge neckline cycle:
    # front_collar (4..12) + back_collar reversed (28..20)
    neck_cycle = front_collar + back_collar[::-1][1:-1] # 16 boundary vertices
    N_neck = len(neck_cycle)

    coll_w = 0.022
    inner_neck = []
    for vn in neck_cycle:
        # Extrude inward towards neck center
        v = bm.verts.new((vn.co.x * 0.88, vn.co.y * 0.85, vn.co.z - coll_w * 0.55))
        inner_neck.append(v)

    for i in range(N_neck):
        i_next = (i + 1) % N_neck
        bm.faces.new([neck_cycle[i], neck_cycle[i_next], inner_neck[i_next], inner_neck[i]])

    # 5. Right & Left Armholes and Draped Sleeves
    # Exactly closed 1D loop of open boundary edges on the torso!
    right_ah = []
    # From top shoulder point top_ring[2] down front edge
    for r in range(N_TOTAL, N_LOWER - 1, -1):
        right_ah.append(torso_rings[r][2])
    # Underarm bottom vertices: 1, 0, 31
    right_ah.append(torso_rings[N_LOWER][1])
    right_ah.append(torso_rings[N_LOWER][0])
    right_ah.append(torso_rings[N_LOWER][31])
    # Up back edge from N_LOWER to N_TOTAL
    for r in range(N_LOWER, N_TOTAL + 1):
        right_ah.append(torso_rings[r][30])

    left_ah = []
    # From top shoulder point top_ring[14] down front edge
    for r in range(N_TOTAL, N_LOWER - 1, -1):
        left_ah.append(torso_rings[r][14])
    # Underarm bottom vertices: 15, 16, 17
    left_ah.append(torso_rings[N_LOWER][15])
    left_ah.append(torso_rings[N_LOWER][16])
    left_ah.append(torso_rings[N_LOWER][17])
    # Up back edge
    for r in range(N_LOWER, N_TOTAL + 1):
        left_ah.append(torso_rings[r][18])

    sleeve_rings_count = 8
    drape_rad = math.radians(52.0)
    cos_d = math.cos(drape_rad)
    sin_d = math.sin(drape_rad)
    fwd_rad = math.radians(4.0)

    a_cuff, b_cuff = solve_ellipse_radii(sleeve_opening, 1.18)

    def loft_sleeve(ah_loop, side_sign):
        N_pts = len(ah_loop)
        cx_ah = sum(v.co.x for v in ah_loop) / N_pts
        cy_ah = sum(v.co.y for v in ah_loop) / N_pts
        cz_ah = sum(v.co.z for v in ah_loop) / N_pts

        cuff_cx = cx_ah + sleeve * cos_d * side_sign
        cuff_cy = cy_ah + sleeve * math.sin(fwd_rad)
        cuff_cz = cz_ah - sleeve * sin_d

        prev_ring = ah_loop

        for r_idx in range(1, sleeve_rings_count + 1):
            t = r_idx / float(sleeve_rings_count)
            t_ease = t * t * (3.0 - 2.0 * t)

            rcx = cx_ah * (1 - t) + cuff_cx * t
            rcy = cy_ah * (1 - t) + cuff_cy * t
            rcz = cz_ah * (1 - t) + cuff_cz * t

            cur_a = a_cuff * t_ease + (armhole_depth * 0.44) * (1 - t_ease)
            cur_b = b_cuff * t_ease + (armhole_depth * 0.40) * (1 - t_ease)

            cur_ring = []
            for i, base_v in enumerate(ah_loop):
                phi = 2.0 * math.pi * i / N_pts
                dx = cur_a * math.cos(phi) * sin_d * side_sign
                dy = cur_b * math.sin(phi)
                dz = -cur_a * math.cos(phi) * cos_d

                # Gentle deltoid convex curve over shoulder cap
                if i < 3 or i > N_pts - 4:
                    deltoid_bump = 0.016 * math.sin(math.pi * min(1.0, t / 0.55))
                    dz += deltoid_bump

                target_x = rcx + dx
                target_y = rcy + dy
                target_z = rcz + dz

                vx = base_v.co.x * (1 - t_ease) + target_x * t_ease
                vy = base_v.co.y * (1 - t_ease) + target_y * t_ease
                vz = base_v.co.z * (1 - t_ease) + target_z * t_ease

                v = bm.verts.new((vx, vy, vz))
                cur_ring.append(v)

            for i in range(N_pts):
                i_next = (i + 1) % N_pts
                if side_sign > 0:
                    bm.faces.new([prev_ring[i], prev_ring[i_next], cur_ring[i_next], cur_ring[i]])
                else:
                    bm.faces.new([prev_ring[i_next], prev_ring[i], cur_ring[i], cur_ring[i_next]])
            prev_ring = cur_ring

    loft_sleeve(right_ah, +1.0)
    loft_sleeve(left_ah, -1.0)

    # Finalize BMesh
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

    # Modifiers
    subsurf = obj.modifiers.new(name="SubdivisionSurface", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    solid = obj.modifiers.new(name="FabricThickness", type='SOLIDIFY')
    solid.thickness = 0.0016
    solid.offset = 0.0
    solid.use_rim = True

    for poly in mesh.polygons:
        poly.use_smooth = True

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
    print(f"Generated seamless model to {output_glb_path}")

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
    build_seamless_tshirt(test_cfg, "storage/generated_models/test_seamless_tshirt.glb")
