from __future__ import annotations

from dataclasses import dataclass

@dataclass(slots=True)
class RenderingSettings:
    limiting_magnitude: float = 6.5