"""Explicit seam pairing rules for garment panels."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SeamRule:
    panel_a: str
    edge_a: str
    panel_b: str
    edge_b: str
    kind: str


CREW_BODY_SEAMS = (
    SeamRule("FrontPanel", "left_side", "BackPanel", "left_side", "side"),
    SeamRule("FrontPanel", "right_side", "BackPanel", "right_side", "side"),
    SeamRule("FrontPanel", "left_shoulder", "BackPanel", "left_shoulder", "shoulder"),
    SeamRule("FrontPanel", "right_shoulder", "BackPanel", "right_shoulder", "shoulder"),
)

