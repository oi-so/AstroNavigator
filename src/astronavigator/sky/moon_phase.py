from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MoonPhaseInfo:
    illuminated_fraction: float
    age_days: float
    phase_angle_deg: float
    phase_name: str
    is_waxing: bool


    @property
    def illumination_percent(self) -> float:
        return self.illuminated_fraction * 100.0