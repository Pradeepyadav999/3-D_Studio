import bpy
import bmesh
import numpy as np

# Run garment builder up to armhole definition
import math

chest = 1.0668
shoulder = 0.4572
length = 0.7366
sleeve = 0.20955
aspect = 2.45

# Copy the exact code from garment_builder:
def solve_ellipse_radii(circ: float, aspect: float = 2.45):
    r = float(aspect)
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

a_hem, b_hem = solve_ellipse_radii(chest * 0.98, aspect * 0.97)
a_waist, b_waist = solve_ellipse_radii(chest * 0.96, aspect)
a_chest, b_chest = solve_ellipse_radii(chest, aspect * 1.01)

z_hem = 0.0
z_waist = length * 0.38
armhole_depth = shoulder * 0.43
z_underarm = length - armhole_depth

shoulder_half_w = shoulder / 2.0
neck_half_w = shoulder_half_w * 0.41
z_hps = length
slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(20.5))
neck_front_drop = 0.082
neck_back_drop = 0.024
z_neck_front_base = z_hps - neck_front_drop
z_neck_back_base = z_hps - neck_back_drop

bm = bmesh.new()

N_COLS = 32
N_RINGS_LOWER = 12
N_RINGS_MID = 4
N_RINGS_TOP = 4

torso_rings = []
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
        x = cur_a * cos_th
        ring.append(bm.verts.new((x, y, vz)))
    torso_rings.append(ring)

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
        ring.append(bm.verts.new((x, y, z_nominal)))
    torso_rings.append(ring)

top_target_coords = [None] * N_COLS
for i in range(2, 15):
    if i <= 5:
        u_sh = (5 - i) / 3.0
        x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
        y = 0.012 + 0.012 * u_sh
        z = z_hps - slope_drop * u_sh
    elif i >= 11:
        u_sh = (i - 11) / 3.0
        x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
        y = 0.012 + 0.012 * u_sh
        z = z_hps - slope_drop * u_sh
    else:
        k = i - 5
        phi = k / 6.0 * math.pi
        x = neck_half_w * math.cos(phi)
        y = 0.012 + 0.055 * (math.sin(phi) ** 0.95)
        z = z_hps - neck_front_drop * (math.sin(phi) ** 0.95)
    top_target_coords[i] = (x, y, z)

for i in range(18, 31):
    if i <= 21:
        u_sh = (21 - i) / 3.0
        x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
        y = -(0.012 + 0.012 * u_sh)
        z = z_hps - slope_drop * u_sh
    elif i >= 27:
        u_sh = (i - 27) / 3.0
        x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
        y = -(0.012 + 0.012 * u_sh)
        z = z_hps - slope_drop * u_sh
    else:
        k = i - 21
        phi = k / 6.0 * math.pi
        x = -neck_half_w * math.cos(phi)
        y = -(0.012 + 0.038 * (math.sin(phi) ** 0.95))
        z = z_hps - neck_back_drop * (math.sin(phi) ** 0.95)
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
                x_interp = v_mid.co.x * (1 - t_ease) + tx * t_ease
            else:
                x_interp = v_mid.co.x * (1 - t_ease) + tx * t_ease
            y_interp = v_mid.co.y * (1 - t_ease) + ty * t_ease
            z_interp = v_mid.co.z * (1 - t_ease) + tz * t_ease
            v = bm.verts.new((x_interp, y_interp, z_interp))
        else:
            v = bm.verts.new((0, 0, z_underarm))
        ring.append(v)
    torso_rings.append(ring)

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

print(f"Right armhole points: {len(right_ah)}, Left armhole points: {len(left_ah)}")
print("\nComparing right_ah reflected (-x, y, z) with left_ah:")
max_dist = 0.0
for i in range(len(right_ah)):
    vr = right_ah[i].co
    vl = left_ah[i].co
    reflected_vr = (-vr.x, vr.y, vr.z)
    dist = math.sqrt((reflected_vr[0] - vl.x)**2 + (reflected_vr[1] - vl.y)**2 + (reflected_vr[2] - vl.z)**2)
    max_dist = max(max_dist, dist)
    print(f"Index {i:2d}: Refl_R=({reflected_vr[0]:.3f}, {reflected_vr[1]:.3f}, {reflected_vr[2]:.3f}) vs L=({vl.x:.3f}, {vl.y:.3f}, {vl.z:.3f}) => Diff={dist:.4f}m")

print(f"\nMAX DISTANCE BETWEEN REFLECTED RIGHT AND LEFT: {max_dist:.4f}m")
