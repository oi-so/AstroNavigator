from __future__ import annotations


from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class TrackingAdjustment:
    ra_offset_arcsec: float = 0.0
    dec_offset_arcsec: float = 0.0
    manual_time_offset_sec: float = 0.0

    def __post_init__(self) -> None:
        values = {
            "ra_offset_arcsec": self.ra_offset_arcsec,
            "dec_offset_arcsec": self.dec_offset_arcsec,
            "manual_time_offset_sec": self.manual_time_offset_sec,
        }

        for name, value in values.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")


    @property
    def has_position_offset(self) -> bool:
        return self.ra_offset_arcsec != 0.0 or self.dec_offset_arcsec != 0.0

    @property
    def has_time_offset(self) -> bool:
        return self.manual_time_offset_sec != 0.0