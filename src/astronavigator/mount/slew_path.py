from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from astronavigator.sky.position import Position


class PierSide(Enum):
    EAST = "EAST"
    WEST = "WEST"
    UNKNOWN = "UNKNOWN"



@dataclass(slots=True)
class SlewPath:
    start: Position
    target: Position
    waypoint: list[Position]

    ra_direction: int
    dec_direction: int

    ra_steps: int
    dec_steps: int

    pier_side: PierSide
    meridian_flip: bool