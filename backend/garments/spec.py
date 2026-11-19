"""Measurement boundary and garment specification types."""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Measure:
    value: float
    unit: Literal["cm", "in"]
    source: Literal["user", "derived"] = "user"
    definition: str = ""

    def cm(self) -> float:
        return self.value * (2.54 if self.unit == "in" else 1.0)


@dataclass(frozen=True)
class GarmentSpec:
    garment_type: Literal["crew_neck"]
    chest: Measure
    shoulder: Measure
    length: Measure

    def __post_init__(self):
        for name in ("chest", "shoulder", "length"):
            value = getattr(self, name).cm()
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.chest.definition not in ("circumference", "flat_width"):
            raise ValueError("chest definition must be circumference or flat_width")
        if self.chest.definition == "flat_width" and self.chest.cm() < 25:
            raise ValueError("flat chest width is outside adult garment range")
        if self.chest.definition == "circumference" and not 60 <= self.chest.cm() <= 200:
            raise ValueError("chest circumference must be between 60 and 200 cm")
        if not 28 <= self.shoulder.cm() <= 75:
            raise ValueError("shoulder must be between 28 and 75 cm")
        if not 45 <= self.length.cm() <= 115:
            raise ValueError("length must be between 45 and 115 cm")

    @property
    def chest_circumference_cm(self) -> float:
        return self.chest.cm() * (2 if self.chest.definition == "flat_width" else 1)

