"""Deterministic panel spacing in metres; no cloth simulation."""
def panel_depth_m(chest_circumference_cm: float) -> float:
    # Cross-section target uses a shallow ellipse. Equal front/back panel spacing
    # contributes the front-to-back depth; dimensions remain explicitly estimated.
    return max(0.12, min(0.30, chest_circumference_cm / 2.45 / 100.0))

