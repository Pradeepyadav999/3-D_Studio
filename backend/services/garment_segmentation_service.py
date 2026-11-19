"""Garment-Specific Image Segmentation Service.
Isolates the actual garment from human model face, hair, neck, skin, arms, hands, trousers, and studio backgrounds.
Generates high-resolution transparent RGBA cutouts and binary segmentation masks for texture mapping and visual inspection.
"""
import os
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional, Tuple

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage"))
PREVIEWS_DIR = os.path.join(STORAGE_DIR, "previews")
os.makedirs(PREVIEWS_DIR, exist_ok=True)


class GarmentSegmentationService:

    @classmethod
    def segment_garment(
        cls,
        image_path: str,
        product_id: str,
        view_type: str = "front"
    ) -> Dict[str, Any]:
        """
        Segments the garment from a product photograph.
        Returns:
            {
                "success": bool,
                "cutout_path": str,
                "cutout_url": str,
                "mask_path": str,
                "mask_url": str,
                "bounding_box": [x1, y1, x2, y2],
                "coverage_pct": float,
                "aspect_ratio": float
            }
        """
        if not image_path or not os.path.exists(image_path):
            return {"success": False, "error": "Image file not found"}

        bgr = cv2.imread(image_path)
        if bgr is None:
            return {"success": False, "error": "Could not decode image"}

        h, w = bgr.shape[:2]

        # Downscale for fast, robust GrabCut iteration
        max_dim = 800
        scale = min(1.0, float(max_dim) / max(h, w))
        sw, sh = int(w * scale), int(h * scale)
        small_bgr = cv2.resize(bgr, (sw, sh), interpolation=cv2.INTER_AREA)

        # 1. Initialize GrabCut Mask with Probable Background
        mask = np.full((sh, sw), cv2.GC_PR_BGD, dtype=np.uint8)

        # 2. Border Background Seeds (outer 4-5% are always studio backdrop)
        b_top = max(2, int(sh * 0.05))
        b_sides = max(2, int(sw * 0.04))
        b_bot = int(sh * 0.88)  # Lower 12% is trousers/jeans/shoes

        mask[0:b_top, :] = cv2.GC_BGD
        mask[:, 0:b_sides] = cv2.GC_BGD
        mask[:, sw - b_sides:] = cv2.GC_BGD
        mask[b_bot:, :] = cv2.GC_BGD

        # 3. Multi-Color-Space Human Skin Detection (YCrCb + HSV)
        ycrcb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2YCrCb)
        cr = ycrcb[:, :, 1]
        cb = ycrcb[:, :, 2]

        hsv = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2HSV)
        s_ch = hsv[:, :, 1]
        v_ch = hsv[:, :, 2]

        # Natural human skin tones across diverse lighting
        is_skin = (
            (cr >= 130) & (cr <= 175) &
            (cb >= 77) & (cb <= 128) &
            (s_ch >= 25) & (v_ch >= 40)
        )

        # Mark Head, Face, and Neck Skin as Definite Background (upper 28% of frame)
        head_neck_y = int(sh * 0.28)
        mask[is_skin & (np.arange(sh)[:, None] < head_neck_y)] = cv2.GC_BGD

        # Mark Arm and Hand Skin as Definite Background on outer lateral regions
        flank_left_x = int(sw * 0.22)
        flank_right_x = int(sw * 0.78)
        mask[is_skin & (
            (np.arange(sw)[None, :] < flank_left_x) |
            (np.arange(sw)[None, :] > flank_right_x)
        )] = cv2.GC_BGD

        # 4. Foreground Seeds: Central Torso Core
        # The central torso area between y=32% and y=70%, x=26% and x=74%
        y_fg1, y_fg2 = int(sh * 0.32), int(sh * 0.70)
        x_fg1, x_fg2 = int(sw * 0.26), int(sw * 0.74)
        torso_core = mask[y_fg1:y_fg2, x_fg1:x_fg2]
        torso_skin = is_skin[y_fg1:y_fg2, x_fg1:x_fg2]
        torso_core[~torso_skin] = cv2.GC_FGD

        # 5. Probable Foreground for upper chest, shoulders, and sleeves
        y_sh1, y_sh2 = int(sh * 0.18), int(sh * 0.80)
        x_sh1, x_sh2 = int(sw * 0.12), int(sw * 0.88)
        sh_region = mask[y_sh1:y_sh2, x_sh1:x_sh2]
        # Only set to PR_FGD if not already marked definite BGD
        sh_region[(sh_region != cv2.GC_BGD) & (sh_region != cv2.GC_FGD)] = cv2.GC_PR_FGD

        # 6. Run GrabCut
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(small_bgr, mask, None, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_MASK)
        except Exception:
            mask = np.where((np.arange(sh)[:, None] >= head_neck_y) & (np.arange(sh)[:, None] < b_bot), cv2.GC_FGD, cv2.GC_BGD)

        # 7. Extract Foreground Binary Mask
        fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

        # Studio white background suppression (any pure studio white pixel > 238 is never garment)
        is_white_studio = (small_bgr[:, :, 0] > 238) & (small_bgr[:, :, 1] > 238) & (small_bgr[:, :, 2] > 238)
        fg_mask[is_white_studio] = 0

        # Post-GrabCut Human Skin Suppression (strictly removes neck, chin, throat, and arm skin)
        fg_mask[is_skin & (np.arange(sh)[:, None] < int(sh * 0.35))] = 0
        fg_mask[is_skin & ((np.arange(sw)[None, :] < int(sw * 0.22)) | (np.arange(sw)[None, :] > int(sw * 0.78)))] = 0

        # Small morphological closing to smooth fabric texture without bridging arm gaps
        kernel_smooth = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel_smooth)

        # 8. Upscale mask to original high resolution with smooth edge anti-aliasing
        full_mask = cv2.resize(fg_mask, (w, h), interpolation=cv2.INTER_LINEAR)
        full_mask = cv2.GaussianBlur(full_mask, (5, 5), 0)

        # 9. Compute garment bounding box
        pts = np.argwhere(full_mask > 128)
        if len(pts) > 100:
            y_min, x_min = pts.min(axis=0)
            y_max, x_max = pts.max(axis=0)
            bbox = [int(x_min), int(y_min), int(x_max), int(y_max)]
            cov = float(len(pts)) / float(w * h) * 100.0
            ar = float(x_max - x_min) / max(1.0, float(y_max - y_min))
        else:
            bbox = [0, 0, w, h]
            cov = 0.0
            ar = 1.0

        # 10. Generate Transparent RGBA Garment Cutout
        rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = full_mask

        cutout_filename = f"{product_id}_{view_type}_cutout.png"
        mask_filename = f"{product_id}_{view_type}_mask.png"
        cutout_path = os.path.join(PREVIEWS_DIR, cutout_filename)
        mask_path = os.path.join(PREVIEWS_DIR, mask_filename)

        cv2.imwrite(cutout_path, rgba)
        cv2.imwrite(mask_path, full_mask)

        return {
            "success": True,
            "cutout_path": cutout_path,
            "cutout_url": f"/storage/previews/{cutout_filename}",
            "mask_path": mask_path,
            "mask_url": f"/storage/previews/{mask_filename}",
            "bounding_box": bbox,
            "coverage_pct": round(cov, 2),
            "aspect_ratio": round(ar, 3)
        }
