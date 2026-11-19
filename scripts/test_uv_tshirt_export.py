import os
import sys
sys.path.insert(0, os.path.abspath("."))
import math
import json
import bpy
import bmesh
from mathutils import Vector
import numpy as np

# Load our garment builder logic and test with UVs
from backend.blender_engine.garment_builder import solve_ellipse_radii

def test_uv_builder():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Use standard size M parameters
    chest = 1.02
    shoulder = 0.44
    length = 0.70
    sleeve = 0.20
    sleeve_type = "short"
    neck_type = "round"
    aspect = 1.54
    waist = chest * 0.95
    hem = chest * 0.98
    sleeve_opening = chest * 0.33

    a_hem, b_hem = solve_ellipse_radii(hem, aspect * 0.97)
    a_waist, b_waist = solve_ellipse_radii(waist, aspect)
    a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.02)

    z_hem = 0.0
    z_waist = length * 0.40
    armhole_depth = max(0.185, shoulder * 0.47)
    z_underarm = length - armhole_depth

    shoulder_half_w = shoulder / 2.0
    neck_half_w = max(0.075, shoulder * 0.20)
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(14.0))
    z_hps = length

    neck_front_drop = 0.085
    neck_back_drop = 0.022
    neck_front_depth_y = 0.065
    neck_back_depth_y = 0.045

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    N_PERIM = 32
    N_LOWER = 10
    N_UPPER = 8

    torso_rings = []
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

    # Stitch lower torso with UV assignment
    for r in range(N_LOWER):
        r1 = torso_rings[r]
        r2 = torso_rings[r + 1]
        for i in range(N_PERIM):
            i_next = (i + 1) % N_PERIM
            face = bm.faces.new([r1[i], r1[i_next], r2[i_next], r2[i]])
            
            # Determine if this face belongs to front panel or back panel
            # Front panel: i from 0 to 15; Back panel: i from 16 to 31
            is_front = (0 <= i < 16)
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = 0.08 + (vz / z_hps) * 0.82
                v_coord = max(0.01, min(0.99, v_coord))
                if is_front:
                    u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38
                else:
                    u_coord = 0.735 + (vx / (2.2 * a_chest)) * 0.38
                u_coord = max(0.01, min(0.99, u_coord))
                loop[uv_layer].uv = Vector((u_coord, v_coord))

    top_target_coords = [None] * N_PERIM
    # Front top
    for i in range(2, 15):
        if i <= 5:
            u_sh = (5 - i) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            y = 0.010 + 0.014 * u_sh
            z = z_hps - slope_drop * u_sh
        elif i >= 11:
            u_sh = (i - 11) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            y = 0.010 + 0.014 * u_sh
            z = z_hps - slope_drop * u_sh
        else:
            k = i - 5
            phi = k / 6.0 * math.pi
            x = neck_half_w * math.cos(phi)
            y = 0.010 + (neck_front_depth_y - 0.010) * (math.sin(phi) ** 0.85)
            z = z_hps - neck_front_drop * (math.sin(phi) ** 0.85)
        top_target_coords[i] = (x, y, z)

    # Back top
    for i in range(18, 31):
        if i <= 21:
            u_sh = (21 - i) / 3.0
            x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
            y = -(0.010 + 0.014 * u_sh)
            z = z_hps - slope_drop * u_sh
        elif i >= 27:
            u_sh = (i - 27) / 3.0
            x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
            y = -(0.010 + 0.014 * u_sh)
            z = z_hps - slope_drop * u_sh
        else:
            k = i - 21
            phi = k / 6.0 * math.pi
            x = -neck_half_w * math.cos(phi)
            y = -(0.010 + (neck_back_depth_y - 0.010) * (math.sin(phi) ** 0.85))
            z = z_hps - neck_back_drop * (math.sin(phi) ** 0.85)
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
                v_coord = 0.08 + (vz / z_hps) * 0.82
                u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), max(0.01, min(0.99, v_coord))))

        for i in range(18, 30):
            face = bm.faces.new([r1[i], r1[i + 1], r2[i + 1], r2[i]])
            for loop in face.loops:
                vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
                v_coord = 0.08 + (vz / z_hps) * 0.82
                u_coord = 0.735 + (vx / (2.2 * a_chest)) * 0.38
                loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), max(0.01, min(0.99, v_coord))))

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
            v_coord = 0.08 + (vz / z_hps) * 0.82
            # Use front u if vy >= 0 else back u
            if vy >= 0:
                u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38
            else:
                u_coord = 0.735 + (vx / (2.2 * a_chest)) * 0.38
            loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), max(0.01, min(0.99, v_coord))))

    for k in range(3):
        f1 = top_ring[11 + k]
        f2 = top_ring[12 + k]
        b1 = top_ring[21 - k]
        b2 = top_ring[20 - k]
        face = bm.faces.new([f1, f2, b2, b1])
        for loop in face.loops:
            vx, vy, vz = loop.vert.co.x, loop.vert.co.y, loop.vert.co.z
            v_coord = 0.08 + (vz / z_hps) * 0.82
            if vy >= 0:
                u_coord = 0.265 - (vx / (2.2 * a_chest)) * 0.38
            else:
                u_coord = 0.735 + (vx / (2.2 * a_chest)) * 0.38
            loop[uv_layer].uv = Vector((max(0.01, min(0.99, u_coord)), max(0.01, min(0.99, v_coord))))

    # Collar band
    neck_boundary = [top_ring[i] for i in range(5, 12)] + [top_ring[i] for i in range(21, 28)]
    N_neck = len(neck_boundary)
    coll_rings = [neck_boundary]
    collar_height = 0.018
    collar_inward = 0.012
    neck_center_y = 0.005

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

    # Sleeves
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
    drape_rad = math.radians(50.0)
    fwd_rad = math.radians(3.5)
    a_cuff, b_cuff = solve_ellipse_radii(sleeve_opening, 1.14)

    def loft_sleeve_with_uv(ah_loop, side_sign, u_offset):
        N_pts = len(ah_loop)
        cx_ah = sum(v.co.x for v in ah_loop) / N_pts
        cy_ah = sum(v.co.y for v in ah_loop) / N_pts
        cz_ah = sum(v.co.z for v in ah_loop) / N_pts
        C_ah = np.array([cx_ah, cy_ah, cz_ah])

        w_dir = np.array([math.cos(drape_rad) * side_sign, math.sin(fwd_rad), -math.sin(drape_rad)])
        w_unit = w_dir / np.linalg.norm(w_dir)
        u1 = np.array([math.sin(drape_rad) * side_sign, 0.0, math.cos(drape_rad)])
        u1 = u1 / np.linalg.norm(u1)
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
            gravity_sag = 0.010 * (t ** 1.8)

            cur_ring = []
            for i in range(N_pts):
                p1_base, p2_base, phi = ah_coords[i]
                cap_weight = math.sin(phi)
                ring_disp = (sleeve * t) * (1.0 + 0.08 * cap_weight * (1.0 - t_ease))
                q1_target = a_cuff * math.cos(phi)
                q2_target = b_cuff * math.sin(phi)
                c1 = p1_base * (1.0 - t_ease) + q1_target * t_ease
                c2 = p2_base * (1.0 - t_ease) + q2_target * t_ease
                V_3d = C_ah + ring_disp * w_unit + np.array([0.0, 0.0, -gravity_sag]) + c1 * u1 + c2 * u2
                cur_ring.append(bm.verts.new(tuple(V_3d)))

            for i in range(N_pts):
                i_next = (i + 1) % N_pts
                if side_sign > 0:
                    face = bm.faces.new([prev_ring[i], prev_ring[i_next], cur_ring[i_next], cur_ring[i]])
                else:
                    face = bm.faces.new([prev_ring[i_next], prev_ring[i], cur_ring[i], cur_ring[i_next]])

                # Assign UV coordinates to sleeve quads
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

    loft_sleeve_with_uv(right_ah, +1.0, 0.05)
    loft_sleeve_with_uv(left_ah, -1.0, 0.55)

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new("ParametricTshirt_UV")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Garment_UV", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Add Subsurf
    subsurf = obj.modifiers.new(name="SubdivisionSurface", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Check UV layer exists
    assert len(mesh.uv_layers) > 0, "UV layer was not created!"
    print(f"Mesh created successfully with UV layer '{mesh.uv_layers[0].name}'. Total faces: {len(mesh.polygons)}")

    # Add textured material
    mat = bpy.data.materials.new("GarmentTexturedMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new('ShaderNodeOutputMaterial')
    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_tex = nodes.new('ShaderNodeTexImage')

    tex_path = os.path.abspath("storage/test_texture.png")
    node_tex.image = bpy.data.images.load(tex_path)

    node_bsdf.inputs['Roughness'].default_value = 0.78
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    obj.data.materials.append(mat)

    out_glb = "storage/test_full_textured_tshirt.glb"
    bpy.ops.export_scene.gltf(
        filepath=out_glb,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_image_format='AUTO'
    )
    print(f"Exported full textured GLB: {out_glb}, size: {os.path.getsize(out_glb)} bytes")

if __name__ == '__main__':
    test_uv_builder()
