"""Closed 2D panel outlines in centimetres, parameterized by measurements."""
from dataclasses import dataclass
import math
from .spec import GarmentSpec


@dataclass(frozen=True)
class Panel:
    name: str
    side: str
    outline: tuple[tuple[float, float], ...]
    grain: tuple[float, float] = (0.0, 1.0)


def crew_body_panels(spec: GarmentSpec) -> tuple[Panel, Panel]:
    chest = spec.chest_circumference_cm
    shoulder = spec.shoulder.cm()
    length = spec.length.cm()
    # Solve Ramanujan's ellipse perimeter for an aspect ratio of 2.45.
    ratio = 2.45
    b = chest / (2 * math.pi * math.sqrt((ratio**2 + 1) / 2))
    for _ in range(40):
        a = ratio*b
        perimeter = math.pi*(3*(a+b)-math.sqrt((3*a+b)*(a+3*b)))
        delta = max(1e-5, b*1e-5)
        ap = ratio*(b+delta)
        cp = math.pi*(3*(ap+b+delta)-math.sqrt((3*ap+b+delta)*(ap+3*(b+delta))))
        b -= (perimeter-chest)/((cp-perimeter)/delta)
    half_width = ratio*b
    neck_half = shoulder * 0.205
    neck_drop = length * 0.12
    arm_depth = max(17.0, shoulder * 0.44)
    # Front/back panels share side/shoulder lengths and deliberately retain neckline
    # and armhole boundary loops for later set-in sleeve and neckband phases.
    front = (
        (-half_width, 0), (half_width, 0), (half_width, length-arm_depth),
        (shoulder/2, length-3.2), (neck_half, length-1.0),
        (0, length), (-neck_half, length-1.0),
        (-shoulder/2, length-3.2), (-half_width, length-arm_depth),
    )
    back = (
        (-half_width, 0), (half_width, 0), (half_width, length-arm_depth),
        (shoulder/2, length-3.2), (neck_half, length-1.0),
        (0, length-1.4), (-neck_half, length-1.0),
        (-shoulder/2, length-3.2), (-half_width, length-arm_depth),
    )
    return (
        Panel("FrontPanel", "front", front),
        Panel("BackPanel", "back", back),
    )

