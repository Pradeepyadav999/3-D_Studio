"""Measurement validation and normalization for 3D Garment Studio."""
from typing import Dict, Any, Tuple, List
from backend.models.schemas import MeasurementValues

class MeasurementValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field

def to_meters(value: float, unit: str) -> float:
    """Convert measurement value to meters."""
    u = unit.lower().strip()
    if u in ["cm", "centimeter", "centimeters"]:
        return value * 0.01
    elif u in ["in", "inch", "inches"]:
        return value * 0.0254
    elif u in ["m", "meter", "meters"]:
        return value
    else:
        # Default assume cm
        return value * 0.01

def validate_and_normalize_measurements(
    measurements: Any,
    unit: str = "cm",
    fit: str = "regular",
    sleeve_type: str = "short"
) -> Tuple[Dict[str, float], List[str]]:
    """
    Validates measurement ranges and calculates complete parametric inputs in meters.
    Returns:
        (measurements_in_meters, warnings)
    """
    if isinstance(measurements, dict):
        measurements = MeasurementValues(**measurements)
    warnings: List[str] = []

    # Convert essential values to cm for uniform sanity checks
    u = unit.lower().strip()
    scale_to_cm = 1.0
    if u in ["in", "inch", "inches"]:
        scale_to_cm = 2.54
    elif u in ["m", "meter", "meters"]:
        scale_to_cm = 100.0

    # Ensure required measurements are present and strictly positive
    if measurements.chest is None or measurements.chest <= 0:
        raise MeasurementValidationError("Chest circumference measurement must be a positive number.", field="chest")
    if measurements.shoulder is None or measurements.shoulder <= 0:
        raise MeasurementValidationError("Shoulder width measurement must be a positive number.", field="shoulder")
    if measurements.length is None or measurements.length <= 0:
        raise MeasurementValidationError("Body length measurement must be a positive number.", field="length")
    if measurements.sleeve is None or measurements.sleeve <= 0:
        raise MeasurementValidationError("Sleeve length measurement must be a positive number.", field="sleeve")

    chest_cm = float(measurements.chest) * scale_to_cm
    shoulder_cm = float(measurements.shoulder) * scale_to_cm
    length_cm = float(measurements.length) * scale_to_cm
    sleeve_cm = float(measurements.sleeve) * scale_to_cm

    # Auto-detect if user entered inch values while unit was left as 'cm'
    # (e.g. chest 34-54 in, shoulder 14-24 in, length 22-38 in)
    if u in ["cm", "centimeter", "centimeters"] and 14.0 <= shoulder_cm <= 25.0 and 32.0 <= chest_cm <= 58.0 and 20.0 <= length_cm <= 38.0:
        warnings.append(
            f"Auto-detected values entered in inches ({measurements.chest}\", {measurements.shoulder}\", {measurements.length}\"). "
            f"Converting to cm."
        )
        chest_cm *= 2.54
        shoulder_cm *= 2.54
        length_cm *= 2.54
        sleeve_cm *= 2.54

    # 1. Chest range validation (circumference)
    # Check if user entered half-chest (e.g. 48-60 cm)
    if chest_cm < 40.0:
        raise MeasurementValidationError(
            f"Chest circumference {chest_cm:.1f} cm is too small. Please check if this is half-chest or invalid value.",
            field="chest"
        )
    elif 40.0 <= chest_cm < 70.0 and chest_cm < shoulder_cm * 1.8:
        # Probable half-chest measurement entered by user without doubling
        warnings.append(
            f"Warning: Chest measurement {measurements.chest} {unit} appears to be a half-chest (width) value. "
            f"Doubling to {measurements.chest * 2} {unit} for circumference."
        )
        chest_cm *= 2.0
    elif chest_cm > 220.0:
        raise MeasurementValidationError(
            f"Chest circumference {chest_cm:.1f} cm exceeds plausible garment limits (max 220 cm).",
            field="chest"
        )

    # 2. Shoulder range validation
    if shoulder_cm < 25.0 or shoulder_cm > 80.0:
        raise MeasurementValidationError(
            f"Shoulder width {shoulder_cm:.1f} cm is out of realistic range (25 - 80 cm).",
            field="shoulder"
        )

    # 3. Length validation
    if length_cm < 35.0 or length_cm > 130.0:
        raise MeasurementValidationError(
            f"Garment length {length_cm:.1f} cm is out of realistic range (35 - 130 cm).",
            field="length"
        )

    # 4. Sleeve length validation
    if sleeve_type == "short":
        if sleeve_cm < 8.0 or sleeve_cm > 55.0:
            raise MeasurementValidationError(
                f"Short sleeve length {sleeve_cm:.1f} cm is out of realistic range (8 - 55 cm).",
                field="sleeve"
            )
    else:
        if sleeve_cm < 30.0 or sleeve_cm > 95.0:
            raise MeasurementValidationError(
                f"Long sleeve length {sleeve_cm:.1f} cm is out of realistic range (30 - 95 cm).",
                field="sleeve"
            )

    # 5. Cross-measurement proportions
    if shoulder_cm * 2.0 > chest_cm * 1.35:
        warnings.append("Shoulder width is unusually wide compared to chest circumference.")

    # Compute complete normalized parameters in meters
    chest_m = chest_cm * 0.01
    shoulder_m = shoulder_cm * 0.01
    length_m = length_cm * 0.01
    sleeve_m = sleeve_cm * 0.01

    # Optional / Derived parameters based on fit
    if measurements.waist is not None:
        waist_m = to_meters(measurements.waist, unit)
    else:
        # Regular fit: subtle natural taper
        if fit == "slim":
            waist_m = chest_m * 0.92
        elif fit == "relaxed":
            waist_m = chest_m * 1.02
        else:  # regular
            waist_m = chest_m * 0.96

    if measurements.hem is not None:
        hem_m = to_meters(measurements.hem, unit)
    else:
        if fit == "slim":
            hem_m = chest_m * 0.95
        elif fit == "relaxed":
            hem_m = chest_m * 1.02
        else:
            hem_m = chest_m * 0.98

    if measurements.neck is not None and measurements.neck > 0:
        val = to_meters(measurements.neck, unit)
        if val > 0.25:
            # User provided neck circumference (> 25 cm) -> convert to neck opening width
            neck_m = (val * 0.46)
        else:
            neck_m = val
    else:
        # Proportional neck opening width: 40% of shoulder span (e.g. ~19.6 cm for 49 cm shoulder)
        neck_m = shoulder_m * 0.40

    if measurements.sleeve_opening is not None:
        sleeve_opening_m = to_meters(measurements.sleeve_opening, unit)
    else:
        # Sleeve opening circumference (cuff)
        sleeve_opening_m = chest_m * 0.35

    normalized = {
        "chest": chest_m,
        "shoulder": shoulder_m,
        "length": length_m,
        "sleeve": sleeve_m,
        "waist": waist_m,
        "hem": hem_m,
        "neck": neck_m,
        "sleeve_opening": sleeve_opening_m,
        "armhole_depth": max(0.18, shoulder_m * 0.48),
        "shoulder_slope_deg": 13.5,
        "neck_front_drop": 0.085,
        "neck_back_drop": 0.025,
        "fabric_thickness": 0.0018  # 1.8mm fabric thickness
    }

    return normalized, warnings
