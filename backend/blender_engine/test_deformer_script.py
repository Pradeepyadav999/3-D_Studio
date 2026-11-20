import bpy
import bmesh
import math
import numpy as np

def run_test(target_chest, target_shoulder, target_length, garment_type="plain_crew"):
    blend_path = f"storage/base_models/{garment_type}_master.blend"
    bpy.ops.wm.open_mainfile(filepath=blend_path)

    obj = bpy.data.objects.get("PlainCrewTShirt") or bpy.data.objects.get("PoloTShirt")
    mesh = obj.data

    # Map groups
    vert_group_names = {}
    for v in mesh.vertices:
        names = {vg.name for vg in obj.vertex_groups if any(g.group == vg.index for g in v.groups)}
        vert_group_names[v.index] = names

    # Base measurements
    z_all = [v.co.z for v in mesh.vertices]
    z_hem_base = min(z_all)
    z_hps_base = max(z_all)
    base_length = z_hps_base - z_hem_base

    # Base shoulder width
    sh_indices = [idx for idx, names in vert_group_names.items() if 'LeftShoulder' in names or 'RightShoulder' in names]
    base_shoulder = max(mesh.vertices[i].co.x for i in sh_indices) - min(mesh.vertices[i].co.x for i in sh_indices)

    # Base chest circumference at z = 0.495
    torso_uarm = [idx for idx, names in vert_group_names.items() if 'Torso' in names and abs(mesh.vertices[idx].co.z - 0.495) < 0.005]
    tw = max(mesh.vertices[i].co.x for i in torso_uarm) - min(mesh.vertices[i].co.x for i in torso_uarm)
    td = max(mesh.vertices[i].co.y for i in torso_uarm) - min(mesh.vertices[i].co.y for i in torso_uarm)
    a_b = tw / 2.0
    b_b = td / 2.0
    h_b = ((a_b - b_b)**2) / ((a_b + b_b)**2)
    base_chest = math.pi * (a_b + b_b) * (1.0 + (3.0 * h_b) / (10.0 + math.sqrt(4.0 - 3.0 * h_b)))

    print(f"\n--- Testing {garment_type.upper()} ---")
    print(f"Base: Chest={base_chest*100:.2f}cm, Shoulder={base_shoulder*100:.2f}cm, Length={base_length*100:.2f}cm")
    print(f"Target: Chest={target_chest*100:.2f}cm, Shoulder={target_shoulder*100:.2f}cm, Length={target_length*100:.2f}cm")

    # Scaling factors
    s_chest = target_chest / base_chest
    delta_shoulder_half = (target_shoulder - base_shoulder) / 2.0
    delta_length = target_length - base_length

    z_underarm = 0.495
    x_neck = 0.092
    x_acromion = 0.230

    # Apply deformation to each vertex
    for v in mesh.vertices:
        names = vert_group_names[v.index]
        orig_x, orig_y, orig_z = v.co.x, v.co.y, v.co.z
        new_x, new_y, new_z = orig_x, orig_y, orig_z

        is_collar = ('Neckline' in names) or ('PoloCollar' in names)
        is_placket = 'PoloPlacket' in names
        is_left_sleeve = 'LeftSleeve' in names
        is_right_sleeve = 'RightSleeve' in names
        is_left_shoulder = 'LeftShoulder' in names
        is_right_shoulder = 'RightShoulder' in names
        is_torso = 'Torso' in names

        # 1. SHOULDER WIDTH DEFORMATION (Lateral shift X)
        if is_collar or is_placket:
            dx = 0.0
        elif is_left_sleeve:
            dx = -delta_shoulder_half
        elif is_right_sleeve:
            dx = delta_shoulder_half
        elif is_left_shoulder or (is_torso and orig_x < -x_neck and orig_z > z_underarm):
            u = max(0.0, min(1.0, (abs(orig_x) - x_neck) / (x_acromion - x_neck)))
            w_sh = 0.5 * (1.0 - math.cos(math.pi * u))
            dx = -delta_shoulder_half * w_sh
        elif is_right_shoulder or (is_torso and orig_x > x_neck and orig_z > z_underarm):
            u = max(0.0, min(1.0, (abs(orig_x) - x_neck) / (x_acromion - x_neck)))
            w_sh = 0.5 * (1.0 - math.cos(math.pi * u))
            dx = delta_shoulder_half * w_sh
        else:
            dx = 0.0
        new_x += dx

        # 2. CHEST CIRCUMFERENCE DEFORMATION (Radial expansion X, Y)
        if is_collar:
            pass
        elif is_placket:
            new_y = orig_y * s_chest
        elif is_left_sleeve or is_right_sleeve:
            s_sl = 1.0 + (s_chest - 1.0) * 0.15
            new_y = orig_y * s_sl
        elif is_torso or ('Hem' in names):
            if orig_z <= z_underarm:
                w_c = 1.0
            else:
                t_up = max(0.0, min(1.0, (orig_z - z_underarm) / (z_hps_base - z_underarm)))
                w_c = 0.5 * (1.0 + math.cos(math.pi * t_up))

            sc_factor = 1.0 + (s_chest - 1.0) * w_c
            new_x = (new_x - dx) * sc_factor + dx
            new_y = orig_y * sc_factor

        # 3. LENGTH DEFORMATION (Vertical shift Z)
        if orig_z >= z_underarm:
            pass
        else:
            t_len = max(0.0, min(1.0, (z_underarm - orig_z) / (z_underarm - z_hem_base)))
            new_z = orig_z - delta_length * t_len

        v.co = (new_x, new_y, new_z)

    mesh.update()

    # Measure deformed mesh
    new_z_all = [v.co.z for v in mesh.vertices]
    actual_length = max(new_z_all) - min(new_z_all)

    actual_sh_indices = [idx for idx, names in vert_group_names.items() if 'LeftShoulder' in names or 'RightShoulder' in names]
    actual_shoulder = max(mesh.vertices[i].co.x for i in actual_sh_indices) - min(mesh.vertices[i].co.x for i in actual_sh_indices)

    torso_uarm_new = [idx for idx, names in vert_group_names.items() if 'Torso' in names and abs(mesh.vertices[idx].co.z - z_underarm) < 0.015]
    tw_new = max(mesh.vertices[i].co.x for i in torso_uarm_new) - min(mesh.vertices[i].co.x for i in torso_uarm_new)
    td_new = max(mesh.vertices[i].co.y for i in torso_uarm_new) - min(mesh.vertices[i].co.y for i in torso_uarm_new)
    a_new = tw_new / 2.0
    b_new = td_new / 2.0
    h_new = ((a_new - b_new)**2) / ((a_new + b_new)**2)
    actual_chest = math.pi * (a_new + b_new) * (1.0 + (3.0 * h_new) / (10.0 + math.sqrt(4.0 - 3.0 * h_new)))

    print(f"Results:")
    print(f"  Chest:    Target={target_chest*100:.2f}cm, Actual={actual_chest*100:.2f}cm, Error={abs(actual_chest - target_chest)*100:.2f}cm")
    print(f"  Shoulder: Target={target_shoulder*100:.2f}cm, Actual={actual_shoulder*100:.2f}cm, Error={abs(actual_shoulder - target_shoulder)*100:.2f}cm")
    print(f"  Length:   Target={target_length*100:.2f}cm, Actual={actual_length*100:.2f}cm, Error={abs(actual_length - target_length)*100:.2f}cm")

run_test(1.12, 0.49, 0.74, "plain_crew")
run_test(1.18, 0.51, 0.76, "polo")
run_test(0.96, 0.43, 0.68, "plain_crew")
