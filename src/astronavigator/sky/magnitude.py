from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Magnitude:
    value: float

    def is_visible(self, limit: float) -> bool:
        return self.value <= limit

    def __format__(self, format_spec: str) -> str:
        return f"{self.value:{format_spec}}"