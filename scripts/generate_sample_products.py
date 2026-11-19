"""Script to generate realistic e-commerce product listings and high-res garment photos for offline demo and testing."""
import os
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SAMPLE_DIR = os.path.abspath("storage/sample_products")
os.makedirs(SAMPLE_DIR, exist_ok=True)

def create_garment_photo(
    width=1200,
    height=1500,
    base_color=(28, 28, 30),
    collar_color=None,
    graphic_type="surf",
    is_back=False,
    texture_noise=0.03
):
    """Generates a high-res studio product photograph of a flat-lay / ghost-mannequin garment."""
    if collar_color is None:
        collar_color = tuple(max(0, min(255, int(c * 0.9))) for c in base_color)

    # Clean studio backdrop (very soft off-white/light gray vignette)
    img = Image.new("RGB", (width, height), (246, 247, 249))
    draw = ImageDraw.Draw(img)

    # Garment dimensions in image space
    cx = width // 2
    cy = height // 2 + 50

    w_chest = 460
    w_hem = 440
    w_shoulder = 580
    y_hps = 240
    y_hem = 1260
    y_underarm = 580
    y_sleeve_end = 820
    w_sleeve = 160

    # Draw soft studio drop shadow under garment
    shadow_mask = Image.new("L", (width, height), 0)
    shadow_draw = ImageDraw.Draw(shadow_mask)

    # Garment polygon coordinates
    # Silhouette points:
    # Top neck left -> shoulder left -> sleeve top left -> sleeve cuff left -> underarm left -> hem left -> hem right -> underarm right -> sleeve cuff right -> sleeve top right -> shoulder right -> top neck right -> collar scoop
    garment_poly = [
        # Neck right to shoulder right
        (cx + 120, y_hps + 15),
        (cx + w_shoulder // 2, y_hps + 80),
        # Right sleeve
        (cx + w_shoulder // 2 + 180, y_sleeve_end - 40),
        (cx + w_shoulder // 2 + 70, y_sleeve_end + 30),
        (cx + w_chest // 2, y_underarm + 40),
        # Right torso to hem
        (cx + w_hem // 2 + 5, y_hem),
        # Hem curve
        (cx, y_hem + 20),
        # Left torso to hem
        (cx - w_hem // 2 - 5, y_hem),
        # Left underarm
        (cx - w_chest // 2, y_underarm + 40),
        # Left sleeve
        (cx - w_shoulder // 2 - 70, y_sleeve_end + 30),
        (cx - w_shoulder // 2 - 180, y_sleeve_end - 40),
        # Left shoulder to neck
        (cx - w_shoulder // 2, y_hps + 80),
        (cx - 120, y_hps + 15),
    ]

    # Draw shadow
    shadow_poly = [(x, y + 25) for (x, y) in garment_poly]
    shadow_draw.polygon(shadow_poly, fill=160)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=30))
    img.paste((215, 218, 224), (0, 0), shadow_mask)

    # Garment body mask
    body_mask = Image.new("L", (width, height), 0)
    body_draw = ImageDraw.Draw(body_mask)
    body_draw.polygon(garment_poly, fill=255)

    # Base fabric surface with soft folds and highlights
    fabric_arr = np.zeros((height, width, 3), dtype=np.float32)
    fabric_arr[:, :] = base_color

    # Subtle vertical cloth drape gradient
    yy, xx = np.mgrid[0:height, 0:width]
    center_dist_x = np.abs(xx - cx) / float(w_chest // 2)
    shading = 1.0 - 0.08 * (center_dist_x ** 1.5) + 0.04 * np.sin((yy - y_hps) * 0.015)
    shading = np.clip(shading, 0.85, 1.10)
    fabric_arr = fabric_arr * shading[:, :, np.newaxis]

    # Micro fabric weave noise
    noise = np.random.normal(0, texture_noise * 255.0, (height, width, 1))
    fabric_arr = np.clip(fabric_arr + noise, 0, 255).astype(np.uint8)
    fabric_img = Image.fromarray(fabric_arr)

    # Paste fabric onto image using garment mask
    img.paste(fabric_img, (0, 0), body_mask)

    # Draw crew collar band
    neck_center_y = y_hps + (45 if not is_back else 25)
    neck_rx = 118
    neck_ry = 65 if not is_back else 35

    collar_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    collar_draw = ImageDraw.Draw(collar_img)

    collar_rgba = (collar_color[0], collar_color[1], collar_color[2], 255)
    collar_draw.ellipse(
        [cx - neck_rx, neck_center_y - neck_ry, cx + neck_rx, neck_center_y + neck_ry],
        outline=collar_rgba,
        width=22
    )

    # Cut out inner neck hole showing studio background
    inner_mask = Image.new("L", (width, height), 0)
    inner_draw = ImageDraw.Draw(inner_mask)
    inner_draw.ellipse(
        [cx - (neck_rx - 18), neck_center_y - (neck_ry - 14), cx + (neck_rx - 18), neck_center_y + (neck_ry - 14)],
        fill=255
    )
    img.paste(collar_img, (0, 0), collar_img)
    img.paste((246, 247, 249), (0, 0), inner_mask)

    # Draw subtle seams
    draw = ImageDraw.Draw(img)
    seam_col = tuple(max(0, int(c * 0.75)) for c in base_color)
    # Shoulder seams
    draw.line([(cx - 120, y_hps + 15), (cx - w_shoulder // 2, y_hps + 80)], fill=seam_col, width=2)
    draw.line([(cx + 120, y_hps + 15), (cx + w_shoulder // 2, y_hps + 80)], fill=seam_col, width=2)
    # Armhole seams
    draw.line([(cx - w_shoulder // 2, y_hps + 80), (cx - w_chest // 2, y_underarm + 40)], fill=seam_col, width=2)
    draw.line([(cx + w_shoulder // 2, y_hps + 80), (cx + w_chest // 2, y_underarm + 40)], fill=seam_col, width=2)
    # Sleeve hem stitch
    draw.line([(cx - w_shoulder // 2 - 180, y_sleeve_end - 40), (cx - w_shoulder // 2 - 70, y_sleeve_end + 30)], fill=seam_col, width=2)
    draw.line([(cx + w_shoulder // 2 + 70, y_sleeve_end + 30), (cx + w_shoulder // 2 + 180, y_sleeve_end - 40)], fill=seam_col, width=2)
    # Bottom hem double stitch
    draw.line([(cx - w_hem // 2, y_hem - 18), (cx + w_hem // 2, y_hem - 18)], fill=seam_col, width=2)
    draw.line([(cx - w_hem // 2, y_hem - 12), (cx + w_hem // 2, y_hem - 12)], fill=seam_col, width=2)

    # If front view and has graphic, render graphic onto chest
    if not is_back and graphic_type != "none":
        render_chest_graphic(img, cx, cy - 110, graphic_type)

    return img

def render_chest_graphic(base_img, cx, cy, graphic_type):
    """Draws rich graphic artwork directly onto garment chest."""
    graphic_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(graphic_layer)

    if graphic_type == "surf":
        # Vintage California Surf Print: Amber & Crimson with waves & sun
        sun_color = (245, 158, 11, 240) # Amber
        coral_color = (239, 68, 68, 230) # Crimson
        teal_color = (20, 184, 166, 230) # Teal
        cream_color = (254, 243, 199, 245) # Warm cream

        # Retro radiant sun
        draw.ellipse([cx - 90, cy - 100, cx + 90, cy + 80], fill=sun_color)

        # Geometric wave bands
        wave_pts = [
            (cx - 150, cy + 30),
            (cx - 80, cy + 10),
            (cx, cy + 40),
            (cx + 80, cy + 15),
            (cx + 150, cy + 45),
            (cx + 150, cy + 110),
            (cx - 150, cy + 110)
        ]
        draw.polygon(wave_pts, fill=coral_color)

        wave_pts2 = [
            (cx - 145, cy + 65),
            (cx - 60, cy + 45),
            (cx + 20, cy + 75),
            (cx + 90, cy + 50),
            (cx + 145, cy + 80),
            (cx + 145, cy + 130),
            (cx - 145, cy + 130)
        ]
        draw.polygon(wave_pts2, fill=teal_color)

        # Typography banner
        draw.rectangle([cx - 160, cy - 135, cx + 160, cy - 90], fill=cream_color)
        draw.text((cx - 145, cy - 130), "PACIFIC COASTLINE", fill=(17, 24, 39), font_size=28)
        draw.text((cx - 100, cy + 135), "CALIFORNIA 1984", fill=cream_color, font_size=24)

    elif graphic_type == "varsity":
        # Athletic Collegiate Brooklyn Crest
        navy_color = (30, 58, 138, 240)
        red_color = (220, 38, 38, 240)
        gold_color = (217, 119, 6, 240)

        # Shield outline
        shield_pts = [
            (cx - 110, cy - 110),
            (cx + 110, cy - 110),
            (cx + 110, cy + 20),
            (cx, cy + 130),
            (cx - 110, cy + 20)
        ]
        draw.polygon(shield_pts, fill=navy_color)
        draw.polygon([(x * 0.9 + cx * 0.1, y * 0.9 + cy * 0.1) for (x, y) in shield_pts], fill=red_color)

        # Big collegiate Letter 'B'
        draw.rectangle([cx - 40, cy - 70, cx - 15, cy + 60], fill=(255, 255, 255, 250))
        draw.ellipse([cx - 30, cy - 70, cx + 45, cy - 5], outline=(255, 255, 255, 250), width=18)
        draw.ellipse([cx - 30, cy - 15, cx + 50, cy + 60], outline=(255, 255, 255, 250), width=18)

        draw.text((cx - 120, cy - 150), "BROOKLYN ATHLETICS", fill=navy_color, font_size=26)
        draw.text((cx - 70, cy + 140), "DIVISION 01", fill=red_color, font_size=22)

    elif graphic_type == "crest":
        # Minimalist Puma style chest badge
        white_col = (255, 255, 255, 240)
        # Left chest placement
        badge_cx = cx - 110
        badge_cy = cy - 60

        draw.polygon([
            (badge_cx - 45, badge_cy + 15),
            (badge_cx - 15, badge_cy - 35),
            (badge_cx + 25, badge_cy - 30),
            (badge_cx + 45, badge_cy + 10),
            (badge_cx + 15, badge_cy + 25),
            (badge_cx - 10, badge_cy + 5)
        ], fill=white_col)
        draw.text((badge_cx - 40, badge_cy + 35), "SPORT", fill=white_col, font_size=20)

    # Composite graphic onto base garment with alpha
    base_img.paste(graphic_layer, (0, 0), graphic_layer)

def generate_samples():
    products = [
        {
            "id": "fk_graphic_crew_black",
            "title": "Roadster Men Graphic Printed Pure Cotton Crew Neck Black T-Shirt",
            "brand": "Roadster",
            "category": "T-Shirts",
            "price": "₹499",
            "rating": 4.3,
            "ratings_count": "18,420",
            "description": "Black printed regular-fit T-shirt with vintage Pacific Coastline graphic on the chest. Crafted from 100% breathable combed cotton with rib knit crew collar for all-day comfort.",
            "specifications": {
                "Fit": "Regular Fit",
                "Neck": "Round / Crew Neck",
                "Sleeve": "Short Sleeve",
                "Fabric": "100% Combed Cotton",
                "Pattern": "Graphic Print",
                "Occasion": "Casual Streetwear",
                "Wash Care": "Machine wash cold with like colors"
            },
            "color_name": "Onyx Black",
            "base_color_hex": "#1C1C1E",
            "base_color_rgb": [28, 28, 30],
            "collar_color_rgb": [20, 20, 22],
            "secondary_colors": ["#F59E0B", "#EF4444", "#14B8A6"],
            "graphic_type": "surf",
            "graphic_description": "Pacific Coastline vintage sun and wave illustration with typography banner across the chest.",
            "neck_type": "round",
            "sleeve_type": "short"
        },
        {
            "id": "fk_vintage_varsity_white",
            "title": "HIGHLANDER Men Typography Print Round Neck White T-Shirt",
            "brand": "Highlander",
            "category": "T-Shirts",
            "price": "₹379",
            "rating": 4.1,
            "ratings_count": "9,850",
            "description": "Classic white regular-fit round-neck T-shirt with varsity athletic Brooklyn crest print. Bio-washed soft cotton fabric with durable ribbed collar.",
            "specifications": {
                "Fit": "Regular Fit",
                "Neck": "Round / Crew Neck",
                "Sleeve": "Short Sleeve",
                "Fabric": "100% Bio-Washed Cotton",
                "Pattern": "Typography & Emblem",
                "Occasion": "Daily Casual",
                "Wash Care": "Machine wash"
            },
            "color_name": "Optical White",
            "base_color_hex": "#F3F4F6",
            "base_color_rgb": [243, 244, 246],
            "collar_color_rgb": [225, 228, 232],
            "secondary_colors": ["#1E3A8A", "#DC2626"],
            "graphic_type": "varsity",
            "graphic_description": "Collegiate Brooklyn athletic shield emblem with varsity lettering on front chest.",
            "neck_type": "round",
            "sleeve_type": "short"
        },
        {
            "id": "fk_minimalist_crest_navy",
            "title": "PUMA Men Solid Classic Crew Neck Navy Blue T-Shirt",
            "brand": "Puma",
            "category": "T-Shirts",
            "price": "₹699",
            "rating": 4.5,
            "ratings_count": "24,310",
            "description": "Navy blue regular-fit solid T-shirt featuring iconic chest sports crest. Soft single jersey cotton with excellent moisture management.",
            "specifications": {
                "Fit": "Regular Fit",
                "Neck": "Round / Crew Neck",
                "Sleeve": "Short Sleeve",
                "Fabric": "100% Pure Single Jersey Cotton",
                "Pattern": "Solid with Chest Crest",
                "Occasion": "Active & Casual",
                "Wash Care": "Machine wash warm"
            },
            "color_name": "Navy Blue",
            "base_color_hex": "#1E293B",
            "base_color_rgb": [30, 41, 59],
            "collar_color_rgb": [24, 32, 46],
            "secondary_colors": ["#FFFFFF"],
            "graphic_type": "crest",
            "graphic_description": "Clean athletic sport crest placed on upper left chest.",
            "neck_type": "round",
            "sleeve_type": "short"
        }
    ]

    for p in products:
        p_dir = os.path.join(SAMPLE_DIR, p["id"])
        os.makedirs(p_dir, exist_ok=True)

        # Generate front photo
        front_img = create_garment_photo(
            base_color=p["base_color_rgb"],
            collar_color=p["collar_color_rgb"],
            graphic_type=p["graphic_type"],
            is_back=False
        )
        front_path = os.path.join(p_dir, "front.jpg")
        front_img.save(front_path, "JPEG", quality=95)

        # Generate back photo
        back_img = create_garment_photo(
            base_color=p["base_color_rgb"],
            collar_color=p["collar_color_rgb"],
            graphic_type="none",
            is_back=True
        )
        back_path = os.path.join(p_dir, "back.jpg")
        back_img.save(back_path, "JPEG", quality=95)

        # Generate detail close-up (crop of chest graphic)
        cx = front_img.width // 2
        cy = front_img.height // 2 - 60
        detail_crop = front_img.crop((cx - 300, cy - 250, cx + 300, cy + 250))
        detail_path = os.path.join(p_dir, "detail.jpg")
        detail_crop.save(detail_path, "JPEG", quality=95)

        # Store product metadata
        p["images"] = {
            "front": f"/storage/sample_products/{p['id']}/front.jpg",
            "back": f"/storage/sample_products/{p['id']}/back.jpg",
            "detail": f"/storage/sample_products/{p['id']}/detail.jpg"
        }
        with open(os.path.join(p_dir, "product.json"), "w") as f:
            json.dump(p, f, indent=2)

        print(f"Generated sample product: {p['id']} -> {p_dir}")

    # Write samples catalog index
    with open(os.path.join(SAMPLE_DIR, "index.json"), "w") as f:
        json.dump([
            {
                "id": p["id"],
                "title": p["title"],
                "brand": p["brand"],
                "price": p["price"],
                "rating": p["rating"],
                "base_color_hex": p["base_color_hex"],
                "color_name": p["color_name"],
                "thumbnail": f"/storage/sample_products/{p['id']}/front.jpg",
                "graphic_description": p["graphic_description"]
            }
            for p in products
        ], f, indent=2)
    print("Sample products index created.")

if __name__ == '__main__':
    generate_samples()
