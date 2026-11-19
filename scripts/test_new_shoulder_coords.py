import sys
sys.path.insert(0, '/Users/pradeepyadav/Desktop/Codiotic/GARMENT_STUDIO')
import math
import numpy as np

chest = 1.0668
shoulder = 0.4572
length = 0.7366
sleeve = 0.2286
neck_circ = 0.4318

shoulder_half_w = shoulder / 2.0
val = neck_circ
neck_half_w = (val * 0.46) / 2.0
z_hps = length
slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(14.5))
neck_front_drop = 0.082
neck_back_drop = 0.024

print("=== NEW CONTINUOUS TOP TARGET COORDS ===")
top_target_coords = [None] * 32

for i in range(2, 15):
    if i <= 5:
        u_sh = (5 - i) / 3.0
        x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
        # Smooth anatomical shoulder slope
        z_drop = slope_drop * (0.20 * u_sh + 0.80 * (u_sh ** 1.3))
        z = z_hps - z_drop
        # Realistic shoulder depth: 3.2 cm at HPS to 5.0 cm at tip
        y = 0.032 + 0.018 * u_sh
        lbl = f"Shoulder R (u={u_sh:.2f})"
    elif i >= 11:
        u_sh = (i - 11) / 3.0
        x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
        z_drop = slope_drop * (0.20 * u_sh + 0.80 * (u_sh ** 1.3))
        z = z_hps - z_drop
        y = 0.032 + 0.018 * u_sh
        lbl = f"Shoulder L (u={u_sh:.2f})"
    else:
        k = i - 5
        phi = k / 6.0 * math.pi
        x = neck_half_w * math.cos(phi)
        sin_phi = math.sin(phi)
        # C1 continuous smooth scoop: sin^2 gives zero vertical slope at HPS!
        s_curve = sin_phi ** 1.7
        y = 0.032 + (0.075 - 0.032) * (sin_phi ** 1.4)
        z = z_hps - neck_front_drop * s_curve
        lbl = f"Neck Scoop (phi={math.degrees(phi):.0f}deg)"
    top_target_coords[i] = (x, y, z)
    print(f"Col {i:2d} ({lbl:24s}): X={x*100:5.2f} cm, Y={y*100:5.2f} cm, Z={z*100:5.2f} cm")

print("\n--- BACK TARGET COORDS ---")
for i in range(18, 31):
    if i <= 21:
        u_sh = (21 - i) / 3.0
        x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
        z_drop = slope_drop * (0.20 * u_sh + 0.80 * (u_sh ** 1.3))
        z = z_hps - z_drop
        y = -(0.032 + 0.018 * u_sh)
        lbl = f"Shoulder L (u={u_sh:.2f})"
    elif i >= 27:
        u_sh = (i - 27) / 3.0
        x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
        z_drop = slope_drop * (0.20 * u_sh + 0.80 * (u_sh ** 1.3))
        z = z_hps - z_drop
        y = -(0.032 + 0.018 * u_sh)
        lbl = f"Shoulder R (u={u_sh:.2f})"
    else:
        k = i - 21
        phi = k / 6.0 * math.pi
        x = -neck_half_w * math.cos(phi)
        sin_phi = math.sin(phi)
        s_curve = sin_phi ** 1.7
        y = -(0.032 + (0.052 - 0.032) * (sin_phi ** 1.4))
        z = z_hps - neck_back_drop * s_curve
        lbl = f"Back Neck (phi={math.degrees(phi):.0f}deg)"
    top_target_coords[i] = (x, y, z)
    print(f"Col {i:2d} ({lbl:24s}): X={x*100:5.2f} cm, Y={y*100:5.2f} cm, Z={z*100:5.2f} cm")
