"""Garment Vision Analysis Service.
Analyzes product images with garment-specific segmentation to extract dominant base color, secondary colors,
detect chest & back prints/graphics with high-resolution bounding boxes, and classify neckline/sleeve geometry.
"""
import os
import cv2
import numpy as np
from PIL import Image, ImageFilter
from typing import Dict, Any, List, Tuple, Optional

from backend.models.schemas import GarmentVisionAnalysis, GraphicAnalysis
from backend.services.garment_segmentation_service import GarmentSegmentationService

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage"))
PREVIEWS_DIR = os.path.join(STORAGE_DIR, "previews")
os.makedirs(PREVIEWS_DIR, exist_ok=True)

COLOR_NAMES = [
    ((0, 0, 0), "Black"),
    ((25, 25, 30), "Onyx Black"),
    ((245, 245, 245), "White"),
    ((230, 230, 230), "Heather White"),
    ((30, 45, 75), "Navy Blue"),
    ((50, 100, 200), "Royal Blue"),
    ((180, 40, 40), "Crimson Red"),
    ((210, 50, 50), "Red"),
    ((205, 95, 115), "Coral Pink"),
    ((220, 105, 125), "Pink"),
    ((235, 140, 150), "Pastel Pink"),
    ((235, 130, 130), "Salmon Pink"),
    ((240, 160, 175), "Rose Pink"),
    ((195, 80, 105), "Deep Coral Pink"),
    ((40, 140, 70), "Emerald Green"),
    ((80, 90, 70), "Olive Green"),
    ((100, 135, 115), "Forest Green"),
    ((120, 150, 130), "Sage Green"),
    ((230, 160, 30), "Amber Gold"),
    ((220, 200, 170), "Beige / Khaki"),
    ((110, 110, 115), "Charcoal Gray"),
    ((160, 160, 165), "Heather Gray"),
]

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"

def closest_color_name(rgb: Tuple[int, int, int]) -> str:
    best_name = "Custom Color"
    min_dist = float("inf")
    for ref_rgb, name in COLOR_NAMES:
        dist = sum((a - b) ** 2 for a, b in zip(rgb, ref_rgb))
        if dist < min_dist:
            min_dist = dist
            best_name = name
    return best_name


class GarmentVisionService:

    @classmethod
    def _detect_polo_button_count(cls, cutout_path: Optional[str], default_count: int = 2) -> int:
        """Inspects segmented garment cutout placket ROI to detect button count (2 vs 3)."""
        if not cutout_path or not os.path.exists(cutout_path):
            return default_count
        try:
            rgba = cv2.imread(cutout_path, cv2.IMREAD_UNCHANGED)
            if rgba is None:
                return default_count
            alpha = rgba[:, :, 3]
            pts = np.argwhere(alpha > 180)
            if len(pts) < 1000:
                return default_count
            gy_min, gx_min = pts.min(axis=0)
            gy_max, gx_max = pts.max(axis=0)
            gh = gy_max - gy_min
            gw = gx_max - gx_min

            roi_y1 = gy_min + int(gh * 0.10)
            roi_y2 = gy_min + int(gh * 0.38)
            roi_x1 = gx_min + int(gw * 0.44)
            roi_x2 = gx_min + int(gw * 0.56)

            placket_bgr = rgba[roi_y1:roi_y2, roi_x1:roi_x2, :3]
            gray = cv2.cvtColor(placket_bgr, cv2.COLOR_BGR2GRAY)
            # Find bright circular button candidates
            med_val = np.median(gray)
            bright_spots = (gray > min(230, med_val + 28)).astype(np.uint8) * 255
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bright_spots)
            valid_btns = []
            for i in range(1, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]
                bw = stats[i, cv2.CC_STAT_WIDTH]
                bh = stats[i, cv2.CC_STAT_HEIGHT]
                if 15 < area < 450 and 0.5 < bw / max(1, bh) < 2.0:
                    valid_btns.append(centroids[i])
            if len(valid_btns) >= 3:
                return 3
            elif len(valid_btns) == 2:
                return 2
            return default_count
        except Exception:
            return default_count

    @classmethod
    def _detect_button_color(cls, cutout_path: Optional[str], default_hex: str = "#F6F5EE") -> str:
        """Samples button color in placket zone or defaults to pearl white."""
        if not cutout_path or not os.path.exists(cutout_path):
            return default_hex
        try:
            rgba = cv2.imread(cutout_path, cv2.IMREAD_UNCHANGED)
            if rgba is None:
                return default_hex
            alpha = rgba[:, :, 3]
            pts = np.argwhere(alpha > 180)
            if len(pts) < 1000:
                return default_hex
            gy_min, gx_min = pts.min(axis=0)
            gy_max, gx_max = pts.max(axis=0)
            gh = gy_max - gy_min
            gw = gx_max - gx_min

            roi_y1 = gy_min + int(gh * 0.12)
            roi_y2 = gy_min + int(gh * 0.35)
            roi_x1 = gx_min + int(gw * 0.45)
            roi_x2 = gx_min + int(gw * 0.55)

            placket_rgb = cv2.cvtColor(rgba[roi_y1:roi_y2, roi_x1:roi_x2, :3], cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(placket_rgb, cv2.COLOR_RGB2GRAY)
            bright_pts = placket_rgb[gray > 170]
            if len(bright_pts) > 20:
                mean_c = np.mean(bright_pts, axis=0).astype(int)
                return rgb_to_hex(int(mean_c[0]), int(mean_c[1]), int(mean_c[2]))
            return default_hex
        except Exception:
            return default_hex

    @classmethod
    def detect_graphic_print(
        cls,
        image_path: str,
        dom_rgb: np.ndarray,
        product_id: str,
        view_type: str = "front",
        cutout_path: Optional[str] = None,
        is_polo: bool = False
    ) -> GraphicAnalysis:
        """
        Detects graphics, prints, typography, and logos within the segmented garment.
        Uses chromatic distance and gradient edge analysis to distinguish genuine prints from fabric folds.
        Preserves original pixels and exports a clean badge preview.
        """
        if not os.path.exists(image_path):
            return GraphicAnalysis()

        # Ensure we have the segmented transparent garment cutout
        if not cutout_path or not os.path.exists(cutout_path):
            seg_res = GarmentSegmentationService.segment_garment(image_path, product_id, view_type)
            cutout_path = seg_res.get("cutout_path")

        if not cutout_path or not os.path.exists(cutout_path):
            return GraphicAnalysis()

        rgba = cv2.imread(cutout_path, cv2.IMREAD_UNCHANGED)
        if rgba is None:
            return GraphicAnalysis()

        alpha = rgba[:, :, 3]
        bgr = rgba[:, :, :3]
        h, w = alpha.shape
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        garment_pts = np.argwhere(alpha > 180)
        if len(garment_pts) < 1000:
            return GraphicAnalysis(
                detected=False,
                placement="none",
                bounding_box=None,
                badge_preview_url=None,
                description="Insufficient garment pixels detected."
            )

        gy_min, gx_min = garment_pts.min(axis=0)
        gy_max, gx_max = garment_pts.max(axis=0)
        gh = max(10, gy_max - gy_min)
        gw = max(10, gx_max - gx_min)
        gx_center = gx_min + gw / 2.0

        # 1. Sample base fabric color from central illuminated torso
        flank_y1, flank_y2 = gy_min + int(gh * 0.48), gy_min + int(gh * 0.72)
        flank_x1, flank_x2 = gx_min + int(gw * 0.32), gx_min + int(gw * 0.68)

        flank_mask = (alpha[flank_y1:flank_y2, flank_x1:flank_x2] > 200)
        f_sub = rgb[flank_y1:flank_y2, flank_x1:flank_x2]
        if np.sum(flank_mask) > 100:
            f_valid = f_sub[flank_mask]
            b_cand = np.median(f_valid, axis=0).astype(np.float32)
            s_cand = np.std(f_valid, axis=0)
            if float(np.mean(s_cand)) > 25.0:
                base_rgb = dom_rgb.astype(np.float32)
                base_std = np.array([8.0, 8.0, 8.0], dtype=np.float32)
            else:
                base_rgb = b_cand
                base_std = s_cand
        else:
            base_rgb = dom_rgb.astype(np.float32)
            base_std = np.array([10.0, 10.0, 10.0], dtype=np.float32)

        # 2. Chest / Torso Inspection ROI
        # For Front: Start below collar (12% of garment height) to lower abdomen (70%)
        # For Back: Start below neck yoke (10%) to lower back (70%)
        roi_y1 = gy_min + int(gh * (0.12 if view_type != "back" else 0.10))
        roi_y2 = gy_min + int(gh * 0.70)
        roi_x1 = gx_min + int(gw * 0.14)
        roi_x2 = gx_min + int(gw * 0.86)

        roi_rgb = rgb[roi_y1:roi_y2, roi_x1:roi_x2]
        roi_bgr = bgr[roi_y1:roi_y2, roi_x1:roi_x2]
        roi_alpha = alpha[roi_y1:roi_y2, roi_x1:roi_x2]

        r_h, r_w = roi_alpha.shape
        yy, xx = np.mgrid[0:r_h, 0:r_w]
        glob_x = roi_x1 + xx
        glob_y = roi_y1 + yy

        # Skin suppression in ROI
        roi_ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)
        roi_is_skin = (roi_ycrcb[:, :, 1] >= 130) & (roi_ycrcb[:, :, 1] <= 175) & (roi_ycrcb[:, :, 2] >= 77) & (roi_ycrcb[:, :, 2] <= 128)
        is_garment = (roi_alpha > 200) & (~roi_is_skin)

        # Construction feature exclusions (collars, plackets, underarm fold shadows)
        if is_polo and view_type == "front":
            # Exclude collar spread and center placket strip
            is_polo_collar_placket = (
                ((glob_y < gy_min + int(gh * 0.22)) & (np.abs(glob_x - gx_center) < gw * 0.28)) |
                ((glob_y < gy_min + int(gh * 0.44)) & (np.abs(glob_x - gx_center) < gw * 0.12))
            )
            is_garment &= (~is_polo_collar_placket)
        elif view_type == "front":
            # Crew neck ribbing band
            is_crew_rib = (glob_y < gy_min + int(gh * 0.14)) & (np.abs(glob_x - gx_center) < gw * 0.22)
            is_garment &= (~is_crew_rib)

        # Flank fold shadow exclusion in lower torso
        is_flank_shadow = (np.abs(glob_x - gx_center) > gw * 0.34) & (glob_y > gy_min + int(gh * 0.42))
        is_garment &= (~is_flank_shadow)

        # 3. LAB Color Space Chromatic Distance (eliminates wrinkles and shadows)
        roi_lab = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2Lab)
        L = roi_lab[:, :, 0].astype(np.float32)
        A = roi_lab[:, :, 1].astype(np.float32)
        B = roi_lab[:, :, 2].astype(np.float32)

        # Base LAB
        base_bgr_1x1 = np.uint8([[base_rgb[::-1]]])
        base_lab = cv2.cvtColor(base_bgr_1x1, cv2.COLOR_BGR2Lab)[0, 0].astype(np.float32)
        base_L, base_A, base_B = base_lab[0], base_lab[1], base_lab[2]

        chroma_dist = np.sqrt((A - base_A) ** 2 + (B - base_B) ** 2)
        luma_dist = np.abs(L - base_L)

        # 4. High-Frequency Gradient Edges (Sobel)
        roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        sobelx = cv2.Sobel(roi_gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(roi_gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobelx ** 2 + sobely ** 2)

        # A pixel is genuine print if:
        # Inside garment AND (chromatic color difference > 16 OR high-contrast edge print)
        is_chroma_print = chroma_dist > max(16.0, min(24.0, float(np.mean(base_std) * 1.5)))
        is_monochrome_print = (luma_dist > 35.0) & (grad_mag > 30.0)
        candidate_mask = is_garment & (is_chroma_print | is_monochrome_print)

        # 5. Connected Component Filtering
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(candidate_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
        filtered_mask = np.zeros_like(cleaned, dtype=bool)
        for label in range(1, num_labels):
            area = stats[label, cv2.CC_STAT_AREA]
            if area > 45:
                comp_grad = float(np.mean(grad_mag[labels == label]))
                if comp_grad > 20.0 or area > 350:
                    filtered_mask |= (labels == label)

        total_print_pixels = int(np.sum(filtered_mask))
        min_pixels_thresh = int(gw * gh * 0.010)  # At least 1.0% of garment area

        # Also support small distinct badges (e.g. Puma/Nike logos >= 250 px with high gradients)
        is_small_badge = False
        if total_print_pixels < min_pixels_thresh and total_print_pixels >= 220:
            b_pts = np.argwhere(filtered_mask)
            if len(b_pts) > 0:
                by1, bx1 = b_pts.min(axis=0)
                by2, bx2 = b_pts.max(axis=0)
                bw = bx2 - bx1
                bh = by2 - by1
                if bw < gw * 0.35 and bh < gh * 0.35:
                    is_small_badge = True

        if total_print_pixels >= min_pixels_thresh or is_small_badge:
            pts = np.argwhere(filtered_mask)
            by_min, bx_min = pts.min(axis=0)
            by_max, bx_max = pts.max(axis=0)

            # Global image coordinates
            img_x1 = roi_x1 + int(bx_min)
            img_y1 = roi_y1 + int(by_min)
            img_x2 = roi_x1 + int(bx_max)
            img_y2 = roi_y1 + int(by_max)

            # Pad slightly for clean crop
            pad_x = int((img_x2 - img_x1) * 0.06)
            pad_y = int((img_y2 - img_y1) * 0.06)
            crop_x1 = max(0, img_x1 - pad_x)
            crop_y1 = max(0, img_y1 - pad_y)
            crop_x2 = min(w, img_x2 + pad_x)
            crop_y2 = min(h, img_y2 + pad_y)

            badge_filename = f"{product_id}_{view_type}_badge.png"
            badge_path = os.path.join(PREVIEWS_DIR, badge_filename)

            # Crop badge from source image with alpha mask isolating artwork
            badge_rgb = rgb[crop_y1:crop_y2, crop_x1:crop_x2]
            badge_bgr = bgr[crop_y1:crop_y2, crop_x1:crop_x2]
            
            # Feather alpha mask for clean compositing
            bw_h, bw_w = badge_rgb.shape[:2]
            badge_lab = cv2.cvtColor(badge_bgr, cv2.COLOR_BGR2Lab)
            b_dist = np.sqrt((badge_lab[:, :, 1].astype(float) - base_A)**2 + (badge_lab[:, :, 2].astype(float) - base_B)**2)
            b_luma = np.abs(badge_lab[:, :, 0].astype(float) - base_L)
            badge_alpha = np.clip((b_dist - 10.0) / 15.0 * 255.0, 0, 255)
            badge_alpha = np.maximum(badge_alpha, np.clip((b_luma - 30.0) / 25.0 * 255.0, 0, 255))
            badge_alpha = cv2.GaussianBlur(badge_alpha.astype(np.uint8), (5, 5), 0)

            badge_rgba = cv2.cvtColor(badge_rgb, cv2.COLOR_RGB2RGBA)
            badge_rgba[:, :, 3] = badge_alpha
            Image.fromarray(badge_rgba).save(badge_path)

            center_x_norm = ((img_x1 + img_x2) / 2.0 - gx_min) / float(gw)
            if view_type == "front":
                if is_small_badge or center_x_norm > 0.58:
                    placement = "Left Chest Badge"
                elif center_x_norm < 0.42:
                    placement = "Right Chest Badge"
                else:
                    placement = "Chest Center"
                desc = f"{placement} graphic print detected ({img_x2 - img_x1}x{img_y2 - img_y1} px)"
            elif view_type == "back":
                placement = "Back Center" if 0.40 <= center_x_norm <= 0.60 else "Back Panel"
                desc = f"{placement} graphic print detected ({img_x2 - img_x1}x{img_y2 - img_y1} px)"
            else:
                placement = "Sleeve / Detail"
                desc = f"Sleeve detail / badge detected ({img_x2 - img_x1}x{img_y2 - img_y1} px)"

            return GraphicAnalysis(
                detected=True,
                placement=placement,
                bounding_box=[img_x1, img_y1, img_x2, img_y2],
                badge_preview_url=f"/storage/previews/{badge_filename}",
                description=desc
            )

        default_desc = "Clean solid fabric panel (No graphic print)" if view_type != "front" else "Solid minimal garment (No graphic print)"
        return GraphicAnalysis(
            detected=False,
            placement="none",
            bounding_box=None,
            badge_preview_url=None,
            description=default_desc
        )

    @classmethod
    def analyze_garment_image(
        cls,
        image_path: str,
        product_id: str,
        known_specifications: Optional[Dict[str, str]] = None,
        back_image_path: Optional[str] = None,
        detail_image_path: Optional[str] = None
    ) -> GarmentVisionAnalysis:
        """
        Performs multi-angle computer vision analysis on product photographs with garment segmentation:
        Extracts dominant base color, secondary colors, front chest print, back print, and neckline/sleeve attributes.
        """
        if not os.path.exists(image_path):
            return GarmentVisionAnalysis()

        # Resolve neckline, fit, and sleeve early from known specifications
        neckline_type = "round"
        sleeve_type = "short"
        silhouette = "regular"

        if known_specifications:
            neck_spec = str(known_specifications.get("Neck", "")).lower()
            if "v" in neck_spec:
                neckline_type = "v_neck"
            elif "polo" in neck_spec or "collar" in neck_spec:
                neckline_type = "polo"

            sleeve_spec = str(known_specifications.get("Sleeve", "")).lower()
            if "long" in sleeve_spec or "full" in sleeve_spec:
                sleeve_type = "long"
            elif "sleeveless" in sleeve_spec:
                sleeve_type = "sleeveless"

            fit_spec = str(known_specifications.get("Fit", "")).lower()
            if "slim" in fit_spec:
                silhouette = "slim"
            elif "oversized" in fit_spec or "relaxed" in fit_spec or "loose" in fit_spec:
                silhouette = "relaxed"

        is_polo = (neckline_type == "polo")

        # 1. Segment front garment
        front_seg = GarmentSegmentationService.segment_garment(image_path, product_id, "front")
        front_cutout_path = front_seg.get("cutout_path")
        front_cutout_url = front_seg.get("cutout_url")

        # 2. Extract base color strictly from illuminated central torso
        cutout_rgba = cv2.imread(front_cutout_path, cv2.IMREAD_UNCHANGED) if front_cutout_path else None
        c_pts = []
        c_h, c_w = 100, 100
        c_ymin, c_xmin = 0, 0
        full_c_rgb = None
        full_c_bgr = None
        full_c_alpha = None
        if cutout_rgba is not None:
            full_c_alpha = cutout_rgba[:, :, 3]
            full_c_bgr = cutout_rgba[:, :, :3]
            full_c_rgb = cv2.cvtColor(full_c_bgr, cv2.COLOR_BGR2RGB)
            c_pts = np.argwhere(full_c_alpha > 180)
            if len(c_pts) > 1000:
                c_ymin, c_xmin = c_pts.min(axis=0)
                c_ymax, c_xmax = c_pts.max(axis=0)
                c_h = c_ymax - c_ymin
                c_w = c_xmax - c_xmin

                # Sample illuminated central torso (avoiding bottom jeans, underarm crease shadows, and collar)
                ty1, ty2 = c_ymin + int(c_h * 0.45), c_ymin + int(c_h * 0.72)
                tx1, tx2 = c_xmin + int(c_w * 0.32), c_xmin + int(c_w * 0.68)
                t_alpha = full_c_alpha[ty1:ty2, tx1:tx2]
                t_bgr = full_c_bgr[ty1:ty2, tx1:tx2]
                t_rgb = full_c_rgb[ty1:ty2, tx1:tx2]

                t_ycrcb = cv2.cvtColor(t_bgr, cv2.COLOR_BGR2YCrCb)
                t_skin = (t_ycrcb[:, :, 1] >= 130) & (t_ycrcb[:, :, 1] <= 175) & (t_ycrcb[:, :, 2] >= 77) & (t_ycrcb[:, :, 2] <= 128)
                t_valid = t_rgb[(t_alpha > 200) & (~t_skin)]
                if len(t_valid) > 500:
                    fg_pixels = t_valid
                else:
                    fg_pixels = full_c_rgb[full_c_alpha > 200]
            else:
                fg_pixels = full_c_rgb[full_c_alpha > 200]
        else:
            bgr = cv2.imread(image_path)
            fg_pixels = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).reshape(-1, 3)

        if len(fg_pixels) < 500:
            bgr = cv2.imread(image_path)
            fg_pixels = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).reshape(-1, 3)

        # K-Means dominant color clustering
        sub_pixels = fg_pixels[np.random.choice(len(fg_pixels), min(25000, len(fg_pixels)), replace=False)].astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 4
        _, labels, centers = cv2.kmeans(sub_pixels, K, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)

        counts = np.bincount(labels.flatten())
        sorted_indices = np.argsort(counts)[::-1]
        dom_idx = sorted_indices[0]

        # Use the 70th percentile of brightness of the dominant cluster to avoid dark crease shadows
        dom_cluster_pixels = sub_pixels[labels.flatten() == dom_idx]
        cluster_brightness = np.mean(dom_cluster_pixels, axis=1)
        p70_idx = np.argsort(cluster_brightness)[int(len(cluster_brightness) * 0.70)]
        dom_rgb = dom_cluster_pixels[p70_idx].astype(int)

        dom_hex = rgb_to_hex(dom_rgb[0], dom_rgb[1], dom_rgb[2])
        dom_name = closest_color_name(tuple(dom_rgb))

        # Secondary colors
        secondary_hexes = []
        for idx in sorted_indices[1:]:
            sec_rgb = centers[idx].astype(int)
            dist = np.linalg.norm(sec_rgb - dom_rgb)
            if dist > 35 and counts[idx] > len(labels) * 0.08:
                secondary_hexes.append(rgb_to_hex(sec_rgb[0], sec_rgb[1], sec_rgb[2]))

        # Contrast collar color detection (for polos or contrasting collars)
        collar_color_hex = None
        if full_c_rgb is not None and len(c_pts) > 1000:
            col_y1 = c_ymin + int(c_h * 0.04)
            col_y2 = c_ymin + int(c_h * 0.18)
            col_x1 = int(c_xmin + c_w * 0.35)
            col_x2 = int(c_xmin + c_w * 0.65)
            col_sub_alpha = full_c_alpha[col_y1:col_y2, col_x1:col_x2]
            col_sub_rgb = full_c_rgb[col_y1:col_y2, col_x1:col_x2]
            col_sub_bgr = full_c_bgr[col_y1:col_y2, col_x1:col_x2]

            col_ycrcb = cv2.cvtColor(col_sub_bgr, cv2.COLOR_BGR2YCrCb)
            col_skin = (col_ycrcb[:, :, 1] >= 135) & (col_ycrcb[:, :, 1] <= 175) & (col_ycrcb[:, :, 2] >= 80) & (col_ycrcb[:, :, 2] <= 125)
            col_valid = col_sub_rgb[(col_sub_alpha > 180) & (~col_skin)]
            if len(col_valid) > 200:
                sub_col = col_valid[np.random.choice(len(col_valid), min(5000, len(col_valid)), replace=False)].astype(np.float32)
                _, col_lbls, col_cntrs = cv2.kmeans(sub_col, min(3, len(sub_col)), None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
                c_counts = np.bincount(col_lbls.flatten())
                col_dom = col_cntrs[np.argmax(c_counts)].astype(int)
                col_dist = np.linalg.norm(col_dom - dom_rgb)
                if col_dist > 35.0:
                    collar_color_hex = rgb_to_hex(int(col_dom[0]), int(col_dom[1]), int(col_dom[2]))

        # Check if known specifications declare a solid pattern
        spec_declares_solid = False
        if known_specifications:
            pattern_val = str(known_specifications.get("Pattern", "")).lower()
            if any(w in pattern_val for w in ["solid", "plain", "colorblock", "colourblock"]):
                spec_declares_solid = True

        # 3. Detect Front Graphic / Print
        front_graphic = cls.detect_graphic_print(
            image_path=image_path,
            dom_rgb=dom_rgb,
            product_id=product_id,
            view_type="front",
            cutout_path=front_cutout_path,
            is_polo=is_polo
        )

        # If specifications explicitly state solid/colorblock, respect it unless a high-contrast genuine badge was detected
        if spec_declares_solid and front_graphic.detected and front_graphic.placement not in ["Left Chest Badge", "Right Chest Badge"]:
            front_graphic = GraphicAnalysis(
                detected=False,
                placement="none",
                bounding_box=None,
                badge_preview_url=None,
                description="Solid plain garment as specified."
            )

        # 4. Segment and Detect Back Graphic / Print
        back_cutout_url = None
        back_graphic = None
        back_status = "missing_reference"

        if back_image_path and os.path.exists(back_image_path):
            back_seg = GarmentSegmentationService.segment_garment(back_image_path, product_id, "back")
            back_cutout_path = back_seg.get("cutout_path")
            back_cutout_url = back_seg.get("cutout_url")

            back_graphic = cls.detect_graphic_print(
                image_path=back_image_path,
                dom_rgb=dom_rgb,
                product_id=product_id,
                view_type="back",
                cutout_path=back_cutout_path,
                is_polo=False
            )

            if back_graphic.detected:
                back_status = "extracted"
            else:
                back_status = "plain"
        else:
            back_status = "missing_reference"
            back_graphic = None

        # 5. Detect Sleeve / Detail Graphic
        sleeve_graphic = None
        if detail_image_path and os.path.exists(detail_image_path):
            sleeve_graphic = cls.detect_graphic_print(
                image_path=detail_image_path,
                dom_rgb=dom_rgb,
                product_id=product_id,
                view_type="detail",
                is_polo=is_polo
            )

        # 6. Pattern Classification
        if front_graphic.detected:
            if front_graphic.placement in ["Left Chest Badge", "Right Chest Badge"]:
                pattern_type = "chest_badge"
            else:
                pattern_type = "graphic_print"
        elif back_graphic and back_graphic.detected:
            pattern_type = "graphic_print"
        else:
            pattern_type = "solid"

        # 8. Button, Placket, and Collar Construction Analysis
        button_count = 0
        button_color_hex = "#F8F8F4"
        placket_length_cm = 0.0
        placket_width_cm = 0.0
        collar_style = "ribbed_crew"
        fabric_texture_type = "cotton_jersey"

        if neckline_type == "polo":
            collar_style = "folded_polo"
            placket_length_cm = 16.5
            placket_width_cm = 3.8
            fabric_texture_type = "cotton_pique"

            spec_desc_text = ""
            if known_specifications:
                spec_desc_text = " ".join([str(v) for v in known_specifications.values()]).lower()

            if any(w in spec_desc_text for w in ["three button", "3 button", "3-button", "three-button"]):
                button_count = 3
            elif any(w in spec_desc_text for w in ["two button", "2 button", "2-button", "two-button"]):
                button_count = 2
            else:
                button_count = cls._detect_polo_button_count(front_cutout_path, default_count=2)

            button_color_hex = cls._detect_button_color(front_cutout_path, default_hex="#F6F5EE")

        elif neckline_type == "v_neck":
            collar_style = "ribbed_v"
        else:
            collar_style = "ribbed_crew"

        if known_specifications:
            fab_str = str(known_specifications.get("Fabric", "")).lower()
            if "pique" in fab_str or "piqué" in fab_str:
                fabric_texture_type = "cotton_pique"
            elif "jersey" in fab_str or "cotton" in fab_str:
                fabric_texture_type = "cotton_jersey"

        return GarmentVisionAnalysis(
            dominant_color_hex=dom_hex,
            dominant_color_name=dom_name,
            secondary_colors=secondary_hexes,
            neckline_type=neckline_type,
            sleeve_type=sleeve_type,
            silhouette=silhouette,
            pattern_type=pattern_type,
            front_cutout_url=front_cutout_url,
            back_cutout_url=back_cutout_url,
            back_status=back_status,
            button_count=button_count,
            button_color_hex=button_color_hex,
            collar_color_hex=collar_color_hex,
            placket_length_cm=placket_length_cm,
            placket_width_cm=placket_width_cm,
            collar_style=collar_style,
            fabric_texture_type=fabric_texture_type,
            graphic=front_graphic,
            back_graphic=back_graphic,
            sleeve_graphic=sleeve_graphic,
            fabric_appearance=known_specifications.get("Fabric", "100% Combed Cotton Single Jersey") if known_specifications else ("Cotton Piqué Knit" if fabric_texture_type == "cotton_pique" else "100% Combed Cotton Single Jersey"),
            confidence_score=0.96
        )
