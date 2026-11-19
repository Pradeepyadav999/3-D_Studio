"""Measurement mathematics and anatomical dimension utilities for 3D Garment Studio.
Pure Python module with no external dependencies (runs in both standard Python and Blender bpy environments).
"""
import math
from typing import Dict, Any, Tuple, Optional


def to_meters(value: float, unit: str) -> float:
    """Convert measurement value to meters."""
    u = unit.lower().strip()
    if u in ["cm", "centimeter", "centimeters"]:
        return value * 0.01
    elif u in ["in", "inch", "inches"]:
        return value * 0.0254
    elif u in ["m", "meter", "meters"]:
        return value
    return value * 0.01


def to_cm(value: float, unit: str) -> float:
    """Convert measurement value to centimeters."""
    u = unit.lower().strip()
    if u in ["in", "inch", "inches"]:
        return value * 2.54
    elif u in ["m", "meter", "meters"]:
        return value * 100.0
    return value


def to_inches(value: float, unit: str) -> float:
    """Convert measurement value to inches."""
    u = unit.lower().strip()
    if u in ["cm", "centimeter", "centimeters"]:
        return value / 2.54
    elif u in ["m", "meter", "meters"]:
        return (value * 100.0) / 2.54
    return value


def resolve_chest_circumference(value: float, measurement_type: str = "circumference") -> float:
    """
    Resolves full garment chest circumference from user input.
    - 'circumference': The 360-degree perimeter around the torso at underarm level.
    - 'flat_width': Pit-to-pit measurement straight across the front of the flattened garment.
      Full circumference = flat_width * 2.0.
    """
    m_type = measurement_type.lower().strip()
    if m_type in ["flat_width", "flat", "width", "pit_to_pit", "half_chest"]:
        return value * 2.0
    return value


def solve_ellipse_radii(circ: float, aspect: float = 2.45) -> Tuple[float, float]:
    """
    Ramanujan's ellipse perimeter approximation solver:
    Perimeter C ≈ π [ 3(a + b) - √((3a + b)(a + 3b)) ]
    where a = aspect * b.
    Solves for semi-major axis 'a' (half-width) and semi-minor axis 'b' (half-depth).
    """
    r = float(aspect)
    # Initial estimate: circle with equivalent perimeter
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


def calculate_anatomical_landmarks(
    chest_m: float,
    shoulder_m: float,
    length_m: float,
    sleeve_m: Optional[float] = None,
    garment_type: str = "basic_crew"
) -> Tuple[Dict[str, float], Dict[str, str]]:
    """
    Derives anatomical garment landmarks from the three core user measurements.
    Distinguishes user-provided values from system-calculated estimates.
    
    Returns:
        (dimensions_dict, sources_dict)
    """
    sources = {
        "chest": "user_provided",
        "shoulder": "user_provided",
        "length": "user_provided"
    }

    # Proportional short sleeve if not entered by user (~43% of shoulder span)
    if sleeve_m is not None and sleeve_m > 0:
        actual_sleeve = sleeve_m
        sources["sleeve"] = "user_provided"
    else:
        actual_sleeve = round(shoulder_m * 0.43, 4)
        sources["sleeve"] = "calculated_estimate"

    shoulder_half_w = shoulder_m / 2.0

    # Anatomical neck opening width
    if garment_type == "polo":
        # Polo neck opening: ~43% of shoulder half-width (to accommodate collar stand)
        neck_half_w = shoulder_half_w * 0.43
    else:
        # Crew-neck round opening: ~41% of shoulder half-width
        neck_half_w = shoulder_half_w * 0.41

    sources["neck_width"] = "calculated_estimate"

    # Natural anatomical shoulder slope: 14.5 degrees
    slope_angle_deg = 14.5
    slope_drop = (shoulder_half_w - neck_half_w) * math.tan(math.radians(slope_angle_deg))
    z_hps = length_m
    z_shoulder_tip = z_hps - slope_drop

    # Armhole depth and vertical underarm junction
    armhole_depth = max(0.18, shoulder_m * 0.44)
    z_underarm = length_m - armhole_depth

    # Subtle natural garment taper (athletic chest to waist and hem)
    waist_m = chest_m * 0.96
    hem_m = chest_m * 0.98
    sources["waist"] = "calculated_estimate"
    sources["hem"] = "calculated_estimate"

    # Sleeve opening (cuff) circumference
    sleeve_opening_m = chest_m * 0.35
    sources["sleeve_opening"] = "calculated_estimate"

    dimensions = {
        "chest": chest_m,
        "shoulder": shoulder_m,
        "length": length_m,
        "sleeve": actual_sleeve,
        "shoulder_half_w": shoulder_half_w,
        "neck_half_w": neck_half_w,
        "slope_drop": slope_drop,
        "slope_angle_deg": slope_angle_deg,
        "z_hps": z_hps,
        "z_shoulder_tip": z_shoulder_tip,
        "z_waist": length_m * 0.38,
        "z_underarm": z_underarm,
        "armhole_depth": armhole_depth,
        "waist": waist_m,
        "hem": hem_m,
        "sleeve_opening": sleeve_opening_m,
        "fabric_thickness": 0.0012  # 1.2 mm realistic cotton jersey / pique thickness
    }

    return dimensions, sources
