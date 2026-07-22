from __future__ import annotations

from dataclasses import dataclass

@dataclass(slots=True)
class RenderingSettings:
    limiting_magnitude: float = 6.5

    minimum_star_radius: float = 1.0
    star_size: float = 5.0
    star_scale: float = 0.5