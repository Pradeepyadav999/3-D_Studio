"""Parametric Torso Geometry Generator with Ramanujan Ellipse Solving."""
import math
import numpy as np
from typing import Dict, Any, List, Tuple

def solve_ellipse_radii(circumference: float, aspect_ratio: float = 1.45) -> Tuple[float, float]:
    """
    Computes semi-major axis (a, lateral width) and semi-minor axis (b, sagittal depth)
    for a given circumference using Ramanujan's ellipse formula:
    C ~ pi * [3(a+b) - sqrt((3a+b)(a+3b))]
    """
    r = aspect_ratio
    # C = pi * b * [3(r+1) - sqrt((3r+1)(r+3))]
    denom = math.pi * (3.0 * (r + 1.0) - math.sqrt((3.0 * r + 1.0) * (r + 3.0)))
    b = circumference / denom
    a = r * b

    # Numerical refinement with Newton-Raphson
    for _ in range(5):
        # Current circumference
        curr_c = math.pi * (3.0 * (a + b) - math.sqrt((3.0 * a + b) * (a + 3.0 * b)))
        error = curr_c - circumference
        if abs(error) < 1e-6:
            break
        # Derivative approx
        delta = 1e-5
        b_plus = b + delta
        a_plus = r * b_plus
        c_plus = math.pi * (3.0 * (a_plus + b_plus) - math.sqrt((3.0 * a_plus + b_plus) * (a_plus + 3.0 * b_plus)))
        dc_db = (c_plus - curr_c) / delta
        b = b - error / dc_db
        a = r * b

    return a, b

def generate_torso_cross_section(
    a: float,
    b: float,
    z: float,
    num_points: int = 40,
    front_bias: float = 0.005
) -> List[Tuple[float, float, float]]:
    """
    Generates 3D points for an elliptical torso ring with subtle natural human contour.
    Parametric angle theta: 0 to 2*pi.
    theta = 0: right side (+X)
    theta = pi/2: front (+Y)
    theta = pi: left side (-X)
    theta = 3*pi/2: back (-Y)
    """
    points = []
    for i in range(num_points):
        theta = 2.0 * math.pi * i / num_points
        # Subtle organic chest shape: front is slightly rounder, back is flatter
        y_scale = 1.05 if math.sin(theta) > 0 else 0.95
        x = a * math.cos(theta)
        y = b * math.sin(theta) * y_scale + (front_bias if math.sin(theta) > 0 else -front_bias * 0.5)
        points.append((round(x, 6), round(y, 6), round(z, 6)))
    return points
