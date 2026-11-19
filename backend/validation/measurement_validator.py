"""Measurement validation and normalization engine for 3D Garment Studio.
Enforces strict dimensional accuracy, explicit chest measurement definitions (circumference vs. flat width),
and tracks user-provided values versus system-calculated estimates.
"""
from typing import Dict, Any, Tuple, List, Optional
from backend.models.schemas import MeasurementValues
from backend.blender_engine.measurement_utils import (
    to_meters, to_cm, resolve_chest_circumference, calculate_anatomical_landmarks
)


class MeasurementValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


def validate_and_normalize_measurements(
    measurements: Any,
    unit: str = "cm",
    garment_type: str = "basic_crew",
    fit: str = "regular",
    sleeve_type: str = "short"
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates dimensional inputs and calculates complete parametric landmarks in meters.
    
    Required User Inputs:
    - Chest (circumference or flat width)
    - Shoulder width (seam to seam)
    - Body length (High Point Shoulder to bottom hem)
    
    Derived / Estimated Parameters:
    - Sleeve length (derived parametrically if not provided)
    - Waist circumference
    - Bottom hem circumference
    - Neck opening width
    
    Returns:
        (measurements_in_meters, warnings)
        where measurements_in_meters includes 'measurement_sources' dictionary.
    """
    if isinstance(measurements, dict):
        measurements = MeasurementValues(**measurements)
    warnings: List[str] = []

    # 1. Validate required core measurements
    if measurements.chest is None or measurements.chest <= 0:
        raise MeasurementValidationError(
            "Chest measurement must be a strictly positive number.",
            field="chest"
        )
    if measurements.shoulder is None or measurements.shoulder <= 0:
        raise MeasurementValidationError(
            "Shoulder seam-to-seam width must be a strictly positive number.",
            field="shoulder"
        )
    if measurements.length is None or measurements.length <= 0:
        raise MeasurementValidationError(
            "Body length (HPS to hem) must be a strictly positive number.",
            field="length"
        )

    u = unit.lower().strip()
    if u not in ["cm", "centimeter", "centimeters", "in", "inch", "inches"]:
        warnings.append(f"Unrecognized unit '{unit}', defaulting to 'cm'.")
        u = "cm"

    # 2. Resolve chest circumference vs flat width
    chest_type = getattr(measurements, "chest_measurement_type", "circumference") or "circumference"
    chest_type = chest_type.lower().strip()
    if chest_type not in ["circumference", "flat_width"]:
        warnings.append(f"Unrecognized chest measurement type '{chest_type}', assuming 'circumference'.")
        chest_type = "circumference"

    raw_chest = float(measurements.chest)
    resolved_circ = resolve_chest_circumference(raw_chest, chest_type)

    # 3. Convert essential values to cm for uniform sanity checks
    circ_cm = to_cm(resolved_circ, u)
    shoulder_cm = to_cm(float(measurements.shoulder), u)
    length_cm = to_cm(float(measurements.length), u)

    # Sanity checks on resolved chest circumference
    if circ_cm < 60.0:
        if chest_type == "circumference":
            raise MeasurementValidationError(
                f"Chest circumference {circ_cm:.1f} cm ({raw_chest} {unit}) is unrealistically small for an adult T-shirt. "
                f"If this was measured flat across the chest, please select 'Flat Chest Width'.",
                field="chest"
            )
        else:
            raise MeasurementValidationError(
                f"Flat chest width {to_cm(raw_chest, u):.1f} cm is unrealistically small for an adult T-shirt.",
                field="chest"
            )
    elif circ_cm > 200.0:
        raise MeasurementValidationError(
            f"Chest circumference {circ_cm:.1f} cm exceeds realistic apparel boundaries (max 200 cm).",
            field="chest"
        )

    # Sanity checks on shoulder seam-to-seam width
    if shoulder_cm < 28.0 or shoulder_cm > 75.0:
        raise MeasurementValidationError(
            f"Shoulder seam-to-seam width {shoulder_cm:.1f} cm ({measurements.shoulder} {unit}) "
            f"is outside realistic adult apparel range (28 - 75 cm / 11 - 30 in).",
            field="shoulder"
        )

    # Sanity checks on body length (HPS to hem)
    if length_cm < 45.0 or length_cm > 115.0:
        raise MeasurementValidationError(
            f"T-shirt length {length_cm:.1f} cm ({measurements.length} {unit}) "
            f"is outside realistic adult apparel range (45 - 115 cm / 18 - 45 in).",
            field="length"
        )

    # Check for anatomical consistency (shoulder span vs chest)
    if shoulder_cm * 2.0 > circ_cm * 1.35:
        warnings.append("Notice: Shoulder width is wide relative to chest circumference.")

    # 4. Optional sleeve validation
    sleeve_m: Optional[float] = None
    if measurements.sleeve is not None:
        if measurements.sleeve <= 0:
            raise MeasurementValidationError(
                "Sleeve measurement must be a strictly positive number.",
                field="sleeve"
            )
        sleeve_cm = to_cm(float(measurements.sleeve), u)
        if sleeve_cm < 8.0 or sleeve_cm > 55.0:
            raise MeasurementValidationError(
                f"Short sleeve length {sleeve_cm:.1f} cm is outside realistic range (8 - 55 cm).",
                field="sleeve"
            )
        sleeve_m = to_meters(float(measurements.sleeve), u)

    # 5. Calculate complete normalized parameters in meters
    chest_m = to_meters(resolved_circ, u)
    shoulder_m = to_meters(float(measurements.shoulder), u)
    length_m = to_meters(float(measurements.length), u)

    # Calculate secondary landmarks & track sources
    normalized, sources = calculate_anatomical_landmarks(
        chest_m=chest_m,
        shoulder_m=shoulder_m,
        length_m=length_m,
        sleeve_m=sleeve_m,
        garment_type=garment_type
    )

    # Store raw user inputs and measurement definitions in metadata
    normalized["raw_user_inputs"] = {
        "chest": raw_chest,
        "chest_measurement_type": chest_type,
        "shoulder": float(measurements.shoulder),
        "length": float(measurements.length),
        "sleeve": float(measurements.sleeve) if measurements.sleeve else None,
        "unit": u
    }
    normalized["measurement_sources"] = sources
    normalized["garment_type"] = garment_type

    return normalized, warnings
