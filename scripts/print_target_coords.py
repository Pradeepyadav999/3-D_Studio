import math

chest = 1.0668
shoulder = 0.4572
length = 0.7366
sleeve = 0.2286
neck_circ = 0.4318

shoulder_half_w = shoulder / 2.0 # 0.2286
val = neck_circ
neck_half_w = (val * 0.46) / 2.0 # 0.099314
z_hps = length # 0.7366
slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(14.5)) # 0.03344
neck_front_drop = 0.082
neck_back_drop = 0.024
z_neck_front_base = z_hps - neck_front_drop # 0.6546
z_neck_back_base = z_hps - neck_back_drop # 0.7126

print(f"Shoulder half w: {shoulder_half_w*100:.2f} cm")
print(f"Neck half w:     {neck_half_w*100:.2f} cm")
print(f"Slope drop:      {slope_drop*100:.2f} cm")
print(f"Z HPS:           {z_hps*100:.2f} cm")
print(f"Z Shoulder Tip:  {(z_hps - slope_drop)*100:.2f} cm")

print("\n--- FRONT TOP TARGET COORDS (Columns 2 to 14) ---")
for i in range(2, 15):
    if i <= 5:
        u_sh = (5 - i) / 3.0
        x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
        y = 0.012 + 0.012 * u_sh
        z = z_hps - slope_drop * u_sh
        lbl = f"Shoulder (u={u_sh:.2f})"
    elif i >= 11:
        u_sh = (i - 11) / 3.0
        x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
        y = 0.012 + 0.012 * u_sh
        z = z_hps - slope_drop * u_sh
        lbl = f"Shoulder L (u={u_sh:.2f})"
    else:
        k = i - 5
        phi = k / 6.0 * math.pi
        x = neck_half_w * math.cos(phi)
        y = 0.012 + 0.055 * (math.sin(phi) ** 0.95)
        z = z_hps - neck_front_drop * (math.sin(phi) ** 0.95)
        lbl = f"Neck Scoop (phi={math.degrees(phi):.0f}deg)"
    print(f"Col {i:2d} ({lbl:24s}): X={x*100:5.2f} cm, Y={y*100:5.2f} cm, Z={z*100:5.2f} cm")

print("\n--- BACK TOP TARGET COORDS (Columns 18 to 30) ---")
for i in range(18, 31):
    if i <= 21:
        u_sh = (21 - i) / 3.0
        x = -(neck_half_w + (shoulder_half_w - neck_half_w) * u_sh)
        y = -(0.012 + 0.012 * u_sh)
        z = z_hps - slope_drop * u_sh
        lbl = f"Shoulder L (u={u_sh:.2f})"
    elif i >= 27:
        u_sh = (i - 27) / 3.0
        x = neck_half_w + (shoulder_half_w - neck_half_w) * u_sh
        y = -(0.012 + 0.012 * u_sh)
        z = z_hps - slope_drop * u_sh
        lbl = f"Shoulder (u={u_sh:.2f})"
    else:
        k = i - 21
        phi = k / 6.0 * math.pi
        x = -neck_half_w * math.cos(phi)
        y = -(0.012 + 0.038 * (math.sin(phi) ** 0.95))
        z = z_hps - neck_back_drop * (math.sin(phi) ** 0.95)
        lbl = f"Back Neck (phi={math.degrees(phi):.0f}deg)"
    print(f"Col {i:2d} ({lbl:24s}): X={x*100:5.2f} cm, Y={y*100:5.2f} cm, Z={z*100:5.2f} cm")
