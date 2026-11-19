"""Automated test suite for Phase 2: Measurement Schema, Validation & Mathematical Engine.
Tests exact Section 19 test cases, explicit chest circumference vs flat width resolution,
unit conversion, and source attribution.
"""
import math
import pytest
from backend.models.schemas import MeasurementValues
from backend.validation.measurement_validator import (
    validate_and_normalize_measurements,
    MeasurementValidationError
)
from backend.blender_engine.measurement_utils import (
    to_meters,
    to_cm,
    to_inches,
    resolve_chest_circumference,
    solve_ellipse_radii
)


class TestMeasurementConversions:

    def test_unit_conversions(self):
        # 1 inch = 0.0254 meters = 2.54 cm
        assert abs(to_meters(1.0, "inch") - 0.0254) < 1e-6
        assert abs(to_cm(1.0, "inch") - 2.54) < 1e-6
        assert abs(to_inches(2.54, "cm") - 1.0) < 1e-6

        # 40 inches = 101.6 cm = 1.016 m
        assert abs(to_cm(40.0, "inch") - 101.6) < 1e-4
        assert abs(to_meters(40.0, "inch") - 1.016) < 1e-4

    def test_ramanujan_ellipse_solver(self):
        target_circ = 1.016  # 40 inches in meters
        aspect = 2.45
        a, b = solve_ellipse_radii(target_circ, aspect)

        # Recompute Ramanujan perimeter from a and b
        computed_c = math.pi * (3.0 * (a + b) - math.sqrt((3.0 * a + b) * (a + 3.0 * b)))
        error = abs(computed_c - target_circ)
        assert error < 1e-6, f"Ramanujan solver error {error} exceeds tolerance"
        assert abs((a / b) - aspect) < 1e-4, "Aspect ratio not preserved"


class TestSection19IllustrativeCases:
    """
    Direct tests of Section 19 test cases:
    - Polo T-shirt, Chest 40 inches full circumference, Shoulder 17 inches, Length 28 inches.
    - Polo T-shirt, Chest 20 inches flat width, Shoulder 17 inches, Length 28 inches.
    Both must resolve to identical garment chest circumference.
    """

    def test_polo_circumference_40_inches(self):
        meas = MeasurementValues(
            chest=40.0,
            chest_measurement_type="circumference",
            shoulder=17.0,
            length=28.0
        )
        normalized, warnings = validate_and_normalize_measurements(
            measurements=meas,
            unit="inch",
            garment_type="polo"
        )

        expected_chest_m = 40.0 * 0.0254  # 1.016 m
        expected_shoulder_m = 17.0 * 0.0254  # 0.4318 m
        expected_length_m = 28.0 * 0.0254  # 0.7112 m

        assert abs(normalized["chest"] - expected_chest_m) < 1e-5
        assert abs(normalized["shoulder"] - expected_shoulder_m) < 1e-5
        assert abs(normalized["length"] - expected_length_m) < 1e-5

        # Check source tracking
        sources = normalized["measurement_sources"]
        assert sources["chest"] == "user_provided"
        assert sources["shoulder"] == "user_provided"
        assert sources["length"] == "user_provided"
        # Sleeve was omitted -> must be explicitly marked as calculated_estimate
        assert sources["sleeve"] == "calculated_estimate"
        assert normalized["sleeve"] > 0

    def test_polo_flat_width_20_inches(self):
        meas = MeasurementValues(
            chest=20.0,
            chest_measurement_type="flat_width",
            shoulder=17.0,
            length=28.0
        )
        normalized, warnings = validate_and_normalize_measurements(
            measurements=meas,
            unit="inch",
            garment_type="polo"
        )

        expected_chest_m = (20.0 * 2.0) * 0.0254  # 1.016 m
        assert abs(normalized["chest"] - expected_chest_m) < 1e-5
        assert normalized["raw_user_inputs"]["chest"] == 20.0
        assert normalized["raw_user_inputs"]["chest_measurement_type"] == "flat_width"

    def test_equivalence_circumference_and_flat_width(self):
        # 40" circumference vs 20" flat width must yield identical 3D chest circumference
        circ_input = MeasurementValues(
            chest=40.0,
            chest_measurement_type="circumference",
            shoulder=17.0,
            length=28.0
        )
        flat_input = MeasurementValues(
            chest=20.0,
            chest_measurement_type="flat_width",
            shoulder=17.0,
            length=28.0
        )

        norm_circ, _ = validate_and_normalize_measurements(circ_input, unit="inch")
        norm_flat, _ = validate_and_normalize_measurements(flat_input, unit="inch")

        assert abs(norm_circ["chest"] - norm_flat["chest"]) < 1e-6
        assert abs(norm_circ["shoulder"] - norm_flat["shoulder"]) < 1e-6
        assert abs(norm_circ["length"] - norm_flat["length"]) < 1e-6


class TestMeasurementBoundaryValidation:

    def test_negative_or_zero_values_raise_error(self):
        with pytest.raises(MeasurementValidationError) as exc_info:
            validate_and_normalize_measurements(
                MeasurementValues(chest=-10.0, shoulder=17.0, length=28.0),
                unit="inch"
            )
        assert exc_info.value.field == "chest"

        with pytest.raises(MeasurementValidationError) as exc_info:
            validate_and_normalize_measurements(
                MeasurementValues(chest=40.0, shoulder=0.0, length=28.0),
                unit="inch"
            )
        assert exc_info.value.field == "shoulder"

    def test_out_of_bounds_raises_error(self):
        # 15 cm circumference is physically impossible for an adult garment
        with pytest.raises(MeasurementValidationError) as exc_info:
            validate_and_normalize_measurements(
                MeasurementValues(chest=15.0, shoulder=40.0, length=70.0),
                unit="cm"
            )
        assert exc_info.value.field == "chest"

        # 300 cm chest exceeds realistic bounds
        with pytest.raises(MeasurementValidationError) as exc_info:
            validate_and_normalize_measurements(
                MeasurementValues(chest=300.0, shoulder=40.0, length=70.0),
                unit="cm"
            )
        assert exc_info.value.field == "chest"

    def test_optional_user_sleeve_is_preserved_as_user_provided(self):
        meas = MeasurementValues(
            chest=106.0,
            shoulder=49.0,
            length=71.0,
            sleeve=22.5
        )
        normalized, _ = validate_and_normalize_measurements(meas, unit="cm")
        assert abs(normalized["sleeve"] - 0.225) < 1e-6
        assert normalized["measurement_sources"]["sleeve"] == "user_provided"
