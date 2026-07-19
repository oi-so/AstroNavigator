from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Magnitude:
    value: float

    def is_visible(self, limit: float) -> bool:
        return self.value <= limit