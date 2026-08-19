from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from astronavigator.sky.position import Position


class PierSide(Enum):
    EAST = "EAST"
    WEST = "WEST"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class MountAxisPosition:
    ra_axis_deg: float
    dec_axis_deg: float


@dataclass(frozen=True, slots=True)
class SlewPath:
    start: Position
    target: Position


    target_pier_side: PierSide
    meridian_flip: bool

    ra_delta_steps: int
    dec_delta_steps: int