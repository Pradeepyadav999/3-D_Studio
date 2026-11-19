"""Texture Extraction and Dual-Panel UV Map Compositing Service.
Extracts original product graphic pixels, logos, typography, and construction details,
and composites them onto the garment's 2048x2048 UV texture layout matching Blender's geometry.
Preserves genuine product pixels with zero AI hallucination or photo distortion.
"""
import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from typing import Dict, Any, Optional, Tuple

from backend.models.schemas import GarmentVisionAnalysis

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage"))
TEXTURES_DIR = os.path.join(STORAGE_DIR, "textures")
PREVIEWS_DIR = os.path.join(STORAGE_DIR, "previews")
os.makedirs(TEXTURES_DIR, exist_ok=True)
os.makedirs(PREVIEWS_DIR, exist_ok=True)


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    return tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))


class TextureExtractionService:

    @classmethod
    def generate_garment_texture_map(
        cls,
        product_id: str,
        front_image_path: str,
        vision_analysis: GarmentVisionAnalysis,
        back_image_path: Optional[str] = None,
        texture_size: int = 2048
    ) -> Dict[str, str]:
        """
        Creates a high-resolution 2048x2048 master texture atlas with matching PBR Normal and Roughness maps
        aligned with Blender's dual-panel parametric UV coordinates.
        Returns: Dict containing paths and URLs for diffuse, normal, and roughness maps.
        """
        base_rgb = hex_to_rgb(vision_analysis.dominant_color_hex)
        out_filename = f"{product_id}_texture.png"
        normal_filename = f"{product_id}_normal.png"
        roughness_filename = f"{product_id}_roughness.png"

        out_path = os.path.join(TEXTURES_DIR, out_filename)
        normal_path = os.path.join(TEXTURES_DIR, normal_filename)
        roughness_path = os.path.join(TEXTURES_DIR, roughness_filename)

        web_url = f"/storage/textures/{out_filename}"
        normal_url = f"/storage/textures/{normal_filename}"
        roughness_url = f"/storage/textures/{roughness_filename}"

        # 1. Base fabric canvas with micro cotton weave texture
        canvas_arr = np.zeros((texture_size, texture_size, 3), dtype=np.float32)
        canvas_arr[:, :] = base_rgb

        is_pique = (getattr(vision_analysis, "fabric_texture_type", "cotton_jersey") == "cotton_pique") or (vision_analysis.neckline_type == "polo")

        if is_pique:
            # Cotton piqué micro weave
            noise = np.random.normal(0, 3.5, (texture_size, texture_size, 1))
            yy, xx = np.mgrid[0:texture_size, 0:texture_size]
            yarn = 2.2 * np.sin(xx * 0.9) * np.cos(yy * 0.9) + 1.2 * np.cos(xx * 1.8)
            canvas_arr = np.clip(canvas_arr + noise + yarn[:, :, np.newaxis], 0, 255).astype(np.uint8)
        else:
            # Cotton single jersey weave
            noise = np.random.normal(0, 2.8, (texture_size, texture_size, 1))
            yy, xx = np.mgrid[0:texture_size, 0:texture_size]
            yarn = 1.4 * np.sin(xx * 1.5) + 1.0 * np.cos(yy * 1.5)
            canvas_arr = np.clip(canvas_arr + noise + yarn[:, :, np.newaxis], 0, 255).astype(np.uint8)

        master_img = Image.fromarray(canvas_arr)
        graphic_boxes = []

        # 2. Extract and composite front graphic / print
        if vision_analysis.graphic and vision_analysis.graphic.detected:
            g_box = cls._composite_graphic_layer(
                master_img=master_img,
                graphic_info=vision_analysis.graphic,
                product_id=product_id,
                view_type="front",
                source_image_path=front_image_path,
                base_rgb=base_rgb,
                texture_size=texture_size,
                is_back=False,
                is_polo=(vision_analysis.neckline_type == "polo")
            )
            if g_box:
                graphic_boxes.append(g_box)

        # 3. Extract and composite back graphic print (ONLY if genuinely detected on back image)
        if back_image_path and os.path.exists(back_image_path):
            if vision_analysis.back_graphic and vision_analysis.back_graphic.detected:
                g_box_b = cls._composite_graphic_layer(
                    master_img=master_img,
                    graphic_info=vision_analysis.back_graphic,
                    product_id=product_id,
                    view_type="back",
                    source_image_path=back_image_path,
                    base_rgb=base_rgb,
                    texture_size=texture_size,
                    is_back=True,
                    is_polo=False
                )
                if g_box_b:
                    graphic_boxes.append(g_box_b)

        # 4. Composite ribbed knit texture onto collar UV band (V in [0.93, 0.99], U in [0.05, 0.95])
        collar_rgb = hex_to_rgb(vision_analysis.collar_color_hex) if getattr(vision_analysis, "collar_color_hex", None) else None
        cls._composite_collar_rib(
            master_img=master_img,
            base_rgb=base_rgb,
            texture_size=texture_size,
            collar_rgb=collar_rgb
        )

        # 5. For polo garments: composite tailored front placket with buttons
        btn_count = getattr(vision_analysis, "button_count", 2) or 2
        btn_color = getattr(vision_analysis, "button_color_hex", "#F8F8F4") or "#F8F8F4"
        if vision_analysis.neckline_type == "polo":
            cls._composite_polo_placket(
                master_img=master_img,
                base_rgb=base_rgb,
                texture_size=texture_size,
                button_count=btn_count,
                button_color_hex=btn_color,
                placket_rgb=collar_rgb
            )

        # 6. Composite sleeve detail if detected
        if vision_analysis.sleeve_graphic and vision_analysis.sleeve_graphic.detected:
            cls._composite_sleeve_detail(
                master_img=master_img,
                graphic_info=vision_analysis.sleeve_graphic,
                product_id=product_id,
                base_rgb=base_rgb,
                texture_size=texture_size
            )

        # Save diffuse texture map
        master_img.save(out_path, format="PNG", optimize=True)

        # 7. Generate PBR Normal Map
        normal_arr = cls._generate_pbr_normal_map(
            texture_size=texture_size,
            is_pique=is_pique,
            is_polo=(vision_analysis.neckline_type == "polo"),
            graphic_boxes=graphic_boxes
        )
        Image.fromarray(normal_arr).save(normal_path, format="PNG", optimize=True)

        # 8. Generate PBR Roughness Map
        roughness_arr = cls._generate_pbr_roughness_map(
            texture_size=texture_size,
            is_pique=is_pique,
            graphic_boxes=graphic_boxes
        )
        Image.fromarray(roughness_arr, mode="L").save(roughness_path, format="PNG", optimize=True)

        return {
            "texture_path": out_path,
            "texture_url": web_url,
            "normal_path": normal_path,
            "normal_url": normal_url,
            "roughness_path": roughness_path,
            "roughness_url": roughness_url
        }

    @classmethod
    def _composite_graphic_layer(
        cls,
        master_img: Image.Image,
        graphic_info: Any,
        product_id: str,
        view_type: str,
        source_image_path: str,
        base_rgb: Tuple[int, int, int],
        texture_size: int,
        is_back: bool = False,
        is_polo: bool = False
    ):
        """
        Composites genuine artwork pixels onto the designated front or back torso UV island.
        Preserves natural aspect ratio, scale, orientation, and placement.
        """
        # Determine badge image path
        badge_path = None
        if graphic_info.badge_preview_url:
            rel = graphic_info.badge_preview_url.lstrip("/")
            test_p = os.path.abspath(rel)
            if os.path.exists(test_p):
                badge_path = test_p

        if not badge_path:
            badge_filename = f"{product_id}_{view_type}_badge.png"
            test_p = os.path.join(PREVIEWS_DIR, badge_filename)
            if os.path.exists(test_p):
                badge_path = test_p

        # Load badge if available with transparent alpha
        if not badge_path or not os.path.exists(badge_path):
            return None

        graphic_img = Image.open(badge_path).convert("RGBA")
        # Ensure badge has transparent pixels isolating the artwork (never paste an opaque photographic rectangle)
        alpha_arr = np.array(graphic_img.getchannel("A"))
        if np.all(alpha_arr > 245) or np.sum(alpha_arr > 20) < 50:
            return None

        w_orig, h_orig = graphic_img.size
        if w_orig <= 5 or h_orig <= 5:
            return

        placement = getattr(graphic_info, "placement", "Chest Center")

        # In UV Space:
        # Front Torso Center: U = 0.265, V = 0.613 -> PIL X = 543, Y = 792
        # Back Torso Center:  U = 0.735, V = 0.613 -> PIL X = 1505, Y = 792
        if not is_back:
            u_center = 0.265
            v_center = 0.613
        else:
            u_center = 0.735
            v_center = 0.613

        target_cx = int(u_center * texture_size)
        target_cy = int((1.0 - v_center) * texture_size)

        # Max bounding box constraints in the 2K UV panel:
        # Torso panel width is ~ 758 px in 2K
        if placement in ["Left Chest Badge", "Right Chest Badge"]:
            max_w = int(texture_size * 0.12)  # ~245 px
            max_h = int(texture_size * 0.12)  # ~245 px
            # Position on wearer's left chest (observer's right = +U in front UV)
            if placement == "Left Chest Badge":
                target_cx = int((0.265 + 0.10) * texture_size)  # U = 0.365 -> X = 747
                target_cy = int((1.0 - 0.67) * texture_size)   # V = 0.67 -> Y = 675
            else:
                target_cx = int((0.265 - 0.10) * texture_size)  # U = 0.165 -> X = 338
                target_cy = int((1.0 - 0.67) * texture_size)
        else:
            # Full Chest / Back Center Graphic
            max_w = int(texture_size * 0.24)  # ~490 px wide
            max_h = int(texture_size * 0.28)  # ~573 px high
            # If polo: shift graphic down slightly to avoid placket overlap
            if is_polo and not is_back:
                target_cy = int((1.0 - 0.52) * texture_size)

        # Scale graphic keeping authentic source aspect ratio
        scale = min(float(max_w) / float(w_orig), float(max_h) / float(h_orig))
        tw = max(10, int(w_orig * scale))
        th = max(10, int(h_orig * scale))

        resized_art = graphic_img.resize((tw, th), Image.Resampling.LANCZOS)

        paste_x = target_cx - tw // 2
        paste_y = target_cy - th // 2

        # Paste artwork cleanly onto UV master map using its transparent alpha channel
        master_img.paste(resized_art, (paste_x, paste_y), resized_art)
        return (paste_x, paste_y, tw, th)

    @classmethod
    def _composite_polo_placket(
        cls,
        master_img: Image.Image,
        base_rgb: Tuple[int, int, int],
        texture_size: int,
        button_count: int = 2,
        button_color_hex: str = "#F8F8F4",
        placket_rgb: Optional[Tuple[int, int, int]] = None
    ):
        """Draws realistic tailored polo placket with seam lines and pearl buttons."""
        draw = ImageDraw.Draw(master_img)
        # Front chest center in UV space is u = 0.265 -> X = 543
        cx = int(0.265 * texture_size)
        half_w = int(0.016 * texture_size)  # ~32 px half width -> 64 px wide placket
        x1 = cx - half_w
        x2 = cx + half_w

        # Placket extends from collar base (Y=246, V=0.88) down to mid-chest (Y=594, V=0.71)
        y1 = int(0.12 * texture_size)
        y2 = int(0.29 * texture_size)

        # Placket background: matching placket_rgb or base_rgb with tailored seam
        use_rgb = placket_rgb if placket_rgb is not None else base_rgb
        p_rgb = tuple(max(0, c - 6) for c in use_rgb)
        draw.rectangle([x1, y1, x2, y2], fill=p_rgb)

        # Outer edge stitch lines
        stitch_rgb = tuple(max(0, c - 24) for c in use_rgb)
        draw.line([(x1, y1), (x1, y2)], fill=stitch_rgb, width=2)
        draw.line([(x2, y1), (x2, y2)], fill=stitch_rgb, width=2)
        draw.line([(x1, y2), (x2, y2)], fill=stitch_rgb, width=2)

        # Center placket overlap line
        center_seam = tuple(max(0, c - 18) for c in use_rgb)
        draw.line([(cx, y1), (cx, y2)], fill=center_seam, width=2)

        # Resolve button color
        btn_rgb = hex_to_rgb(button_color_hex) if button_color_hex else (235, 233, 226)

        # Buttons and buttonholes
        if button_count >= 3:
            btn_y_positions = [
                int(0.155 * texture_size),
                int(0.205 * texture_size),
                int(0.255 * texture_size)
            ]
        else:
            btn_y_positions = [
                int(0.170 * texture_size),
                int(0.235 * texture_size)
            ]

        btn_r = int(0.006 * texture_size)
        for by in btn_y_positions:
            # Button foundation shadow
            draw.ellipse(
                [(cx - btn_r - 1, by - btn_r - 1), (cx + btn_r + 1, by + btn_r + 1)],
                fill=tuple(max(0, c - 30) for c in base_rgb)
            )
            # Pearl button disc
            draw.ellipse(
                [(cx - btn_r, by - btn_r), (cx + btn_r, by + btn_r)],
                fill=btn_rgb,
                outline=(160, 155, 145),
                width=2
            )
            # Button rim inner ring
            ir = max(1, btn_r - 2)
            draw.ellipse(
                [(cx - ir, by - ir), (cx + ir, by + ir)],
                outline=(195, 190, 180),
                width=1
            )
            # Center thread holes
            draw.ellipse([(cx - 2, by - 2), (cx - 1, by - 1)], fill=(70, 70, 70))
            draw.ellipse([(cx + 1, by + 1), (cx + 2, by + 2)], fill=(70, 70, 70))

    @classmethod
    def _generate_pbr_normal_map(
        cls,
        texture_size: int,
        is_pique: bool,
        is_polo: bool,
        graphic_boxes: list
    ) -> np.ndarray:
        """
        Generates 2048x2048 tangent-space PBR normal map (R=X, G=Y, B=Z).
        Produces authentic micro-textile relief: piqué honeycomb waffle or single jersey knit grain,
        collar ribbing indentations, placket seams, and graphic print tactile ink relief.
        """
        normal_arr = np.zeros((texture_size, texture_size, 3), dtype=np.uint8)
        normal_arr[:, :, 0] = 128
        normal_arr[:, :, 1] = 128
        normal_arr[:, :, 2] = 255

        yy, xx = np.mgrid[0:texture_size, 0:texture_size].astype(np.float32)

        if is_pique:
            # 2D cellular pique waffle pattern with diagonal micro interlacing
            w_x = 12.0 * np.sin(xx * 0.45) * np.cos(yy * 0.45)
            w_y = 12.0 * np.cos(xx * 0.45) * np.sin(yy * 0.45)
            normal_arr[:, :, 0] = np.clip(128.0 + w_x, 0, 255).astype(np.uint8)
            normal_arr[:, :, 1] = np.clip(128.0 - w_y, 0, 255).astype(np.uint8)
            normal_arr[:, :, 2] = 250
        else:
            # Cotton jersey vertical rib wales
            w_x = 8.0 * np.sin(xx * 1.5)
            w_y = 2.0 * np.cos(yy * 0.8)
            normal_arr[:, :, 0] = np.clip(128.0 + w_x, 0, 255).astype(np.uint8)
            normal_arr[:, :, 1] = np.clip(128.0 - w_y, 0, 255).astype(np.uint8)
            normal_arr[:, :, 2] = 252

        # Collar ribbing normal grooves (V in [0.92, 0.99] -> Y in [20, 160])
        c_y1 = int(0.01 * texture_size)
        c_y2 = int(0.08 * texture_size)
        c_x = np.arange(texture_size).astype(np.float32)
        rib_mod = 22.0 * np.sin(c_x * (2.0 * np.pi / 4.0))
        normal_arr[c_y1:c_y2, :, 0] = np.clip(128.0 + rib_mod[np.newaxis, :], 0, 255).astype(np.uint8)

        # Collar ditch seam (groove where collar attaches to body)
        ditch_y = int(0.08 * texture_size)
        normal_arr[ditch_y - 2:ditch_y + 2, :, 1] = 75
        normal_arr[ditch_y + 2:ditch_y + 4, :, 1] = 185

        # Pacdora-style subtle organic fabric drape folds (radiating from underarms across torso)
        # Front panel drape waves
        d_fl = 8.0 * np.sin((xx - 200.0) * 0.016 + (yy - 650.0) * 0.022) * np.exp(-(((xx - 450.0) / 320.0) ** 2 + ((yy - 950.0) / 400.0) ** 2))
        d_fr = 8.0 * np.sin((900.0 - xx) * 0.016 + (yy - 650.0) * 0.022) * np.exp(-(((xx - 650.0) / 320.0) ** 2 + ((yy - 950.0) / 400.0) ** 2))
        # Back panel drape waves
        d_bl = 8.0 * np.sin((xx - 1200.0) * 0.016 + (yy - 650.0) * 0.022) * np.exp(-(((xx - 1450.0) / 320.0) ** 2 + ((yy - 950.0) / 400.0) ** 2))
        d_br = 8.0 * np.sin((1900.0 - xx) * 0.016 + (yy - 650.0) * 0.022) * np.exp(-(((xx - 1650.0) / 320.0) ** 2 + ((yy - 950.0) / 400.0) ** 2))
        total_drape_x = d_fl - d_fr + d_bl - d_br
        total_drape_y = (d_fl + d_fr + d_bl + d_br) * 0.8
        normal_arr[:, :, 0] = np.clip(normal_arr[:, :, 0].astype(np.float32) + total_drape_x, 0, 255).astype(np.uint8)
        normal_arr[:, :, 1] = np.clip(normal_arr[:, :, 1].astype(np.float32) - total_drape_y, 0, 255).astype(np.uint8)

        # Twin-needle parallel topstitches at bottom hem (Y in [1865, 1875])
        stitch_dash = (xx % 12.0 < 8.0).astype(np.float32)
        for stitch_y in [int(0.915 * texture_size), int(0.920 * texture_size)]:
            # Front & back panels
            for x_range in [(int(0.06 * texture_size), int(0.48 * texture_size)), (int(0.52 * texture_size), int(0.94 * texture_size))]:
                sx1, sx2 = x_range
                normal_arr[stitch_y - 1:stitch_y + 1, sx1:sx2, 1] = np.clip(128.0 - 55.0 * stitch_dash[stitch_y, sx1:sx2], 0, 255).astype(np.uint8)
                normal_arr[stitch_y + 1:stitch_y + 3, sx1:sx2, 1] = np.clip(128.0 + 55.0 * stitch_dash[stitch_y, sx1:sx2], 0, 255).astype(np.uint8)

        # Twin-needle parallel topstitches at sleeve cuffs (Y in [1920, 1930])
        for cuff_y in [int(0.940 * texture_size), int(0.945 * texture_size)]:
            for x_range in [(int(0.06 * texture_size), int(0.44 * texture_size)), (int(0.56 * texture_size), int(0.94 * texture_size))]:
                sx1, sx2 = x_range
                normal_arr[cuff_y - 1:cuff_y + 1, sx1:sx2, 1] = np.clip(128.0 - 55.0 * stitch_dash[cuff_y, sx1:sx2], 0, 255).astype(np.uint8)
                normal_arr[cuff_y + 1:cuff_y + 3, sx1:sx2, 1] = np.clip(128.0 + 55.0 * stitch_dash[cuff_y, sx1:sx2], 0, 255).astype(np.uint8)

        # Placket seam groove if polo
        if is_polo:
            cx = int(0.265 * texture_size)
            hw = int(0.016 * texture_size)
            py1 = int(0.12 * texture_size)
            py2 = int(0.29 * texture_size)
            # Left seam
            normal_arr[py1:py2, cx - hw - 2:cx - hw + 2, 0] = 70
            # Right seam
            normal_arr[py1:py2, cx + hw - 2:cx + hw + 2, 0] = 186
            # Bottom seam
            normal_arr[py2 - 2:py2 + 2, cx - hw:cx + hw, 1] = 70

        # Graphic print ink tactile relief (raised screen print ink edge)
        for box in graphic_boxes:
            bx, by, bw, bh = box
            if bw > 10 and bh > 10:
                # Top edge
                normal_arr[max(0, by - 2):by + 2, max(0, bx):min(texture_size, bx + bw), 1] = 190
                # Bottom edge
                normal_arr[max(0, by + bh - 2):min(texture_size, by + bh + 2), max(0, bx):min(texture_size, bx + bw), 1] = 65
                # Left edge
                normal_arr[max(0, by):min(texture_size, by + bh), max(0, bx - 2):bx + 2, 0] = 190
                # Right edge
                normal_arr[max(0, by):min(texture_size, by + bh), max(0, bx + bw - 2):min(texture_size, bx + bw + 2), 0] = 65

        return normal_arr

    @classmethod
    def _generate_pbr_roughness_map(
        cls,
        texture_size: int,
        is_pique: bool,
        graphic_boxes: list
    ) -> np.ndarray:
        """
        Generates 2048x2048 grayscale PBR roughness map:
        - Base cotton fabric: 218 (~0.85 roughness, matte textile scattering, non-plastic).
        - Collar rib: 225 (~0.88 roughness).
        - Screen-printed graphic artwork: 150 (~0.58 roughness, satin ink sheen).
        """
        base_rough = 222 if is_pique else 216
        rough_arr = np.full((texture_size, texture_size), base_rough, dtype=np.uint8)

        # Collar rib
        c_y1 = int(0.01 * texture_size)
        c_y2 = int(0.08 * texture_size)
        rough_arr[c_y1:c_y2, :] = 226

        # Topstitch seams: subtle roughness variation (matte thread)
        for stitch_y in [int(0.915 * texture_size), int(0.920 * texture_size), int(0.940 * texture_size), int(0.945 * texture_size)]:
            rough_arr[stitch_y - 1:stitch_y + 2, :] = 232

        # Graphic print regions: smoother satin finish
        for box in graphic_boxes:
            bx, by, bw, bh = box
            y1 = max(0, by)
            y2 = min(texture_size, by + bh)
            x1 = max(0, bx)
            x2 = min(texture_size, bx + bw)
            if y2 > y1 and x2 > x1:
                rough_arr[y1:y2, x1:x2] = 150

        return rough_arr

    @classmethod
    def _composite_collar_rib(
        cls,
        master_img: Image.Image,
        base_rgb: Tuple[int, int, int],
        texture_size: int,
        collar_rgb: Optional[Tuple[int, int, int]] = None
    ):
        """Draws realistic ribbed knit pattern on the collar UV band."""
        c_x1 = int(0.04 * texture_size)
        c_x2 = int(0.96 * texture_size)
        c_y1 = int((1.0 - 0.99) * texture_size)
        c_y2 = int((1.0 - 0.92) * texture_size)

        w = c_x2 - c_x1
        h = c_y2 - c_y1
        if w <= 0 or h <= 0:
            return

        use_col = collar_rgb if collar_rgb is not None else base_rgb
        collar_arr = np.zeros((h, w, 3), dtype=np.float32)
        c_rgb = np.array([max(0, c - 10) for c in use_col], dtype=np.float32)
        collar_arr[:, :] = c_rgb

        # Vertical 1x1 rib wales
        xx = np.arange(w)
        rib_mod = 12.0 * np.sin(xx * (2.0 * np.pi / 4.0))[:, np.newaxis].T
        collar_arr = np.clip(collar_arr + rib_mod[:, :, np.newaxis], 0, 255).astype(np.uint8)

        collar_patch = Image.fromarray(collar_arr)
        master_img.paste(collar_patch, (c_x1, c_y1))

    @classmethod
    def _composite_sleeve_detail(
        cls,
        master_img: Image.Image,
        graphic_info: Any,
        product_id: str,
        base_rgb: Tuple[int, int, int],
        texture_size: int
    ):
        """Composites sleeve badge or stripe onto sleeve UV islands (bottom strip)."""
        badge_path = os.path.join(PREVIEWS_DIR, f"{product_id}_detail_badge.png")
        if not os.path.exists(badge_path):
            return

        art = Image.open(badge_path).convert("RGBA")
        # Sleeve UV band is at bottom Y in [1900, 2030]
        # Right sleeve: X in [200, 800], Left sleeve: X in [1200, 1800]
        sy = int(0.95 * texture_size)
        sx = int(0.25 * texture_size)
        scale = min(120.0 / art.width, 80.0 / art.height)
        rw, rh = int(art.width * scale), int(art.height * scale)
        res_art = art.resize((rw, rh), Image.Resampling.LANCZOS)
        master_img.paste(res_art, (sx - rw // 2, sy - rh // 2), res_art)
