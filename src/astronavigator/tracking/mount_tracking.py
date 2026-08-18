from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math

from astronavigator.sky.position import Position


@dataclass(frozen=True, slots=True)
class TrackingRateCommand:
    requested_ra_rate_deg_per_sec: float
    requested_dec_rate_deg_per_sec: float

    applied_ra_rate_deg_per_sec: float
    applied_dec_rate_deg_per_sec: float

    def __post_init__(self) -> None:
        values = {
            "requested_ra_rate_deg_per_sec": (
                self.requested_ra_rate_deg_per_sec
            ),
            "requested_dec_rate_deg_per_sec": (
                self.requested_dec_rate_deg_per_sec
            ),
            "applied_ra_rate_deg_per_sec": (
                self.applied_ra_rate_deg_per_sec
            ),
            "applied_dec_rate_deg_per_sec": (
                self.applied_dec_rate_deg_per_sec
            ),
        }

        for name, value in values.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")

    @property
    def ra_saturated(self) -> bool:
        return not math.isclose(
            self.requested_ra_rate_deg_per_sec,
            self.applied_ra_rate_deg_per_sec,
            abs_tol=1e-12,
        )

    @property
    def dec_saturated(self) -> bool:
        return not math.isclose(
            self.requested_dec_rate_deg_per_sec,
            self.applied_dec_rate_deg_per_sec,
            abs_tol=1e-12,
        )

    @property
    def is_saturated(self) -> bool:
        return self.ra_saturated or self.dec_saturated


class MountTrackingBackend(ABC):
    @property
    @abstractmethod
    def maximum_ra_rate_deg_per_sec(self) -> float:
        ...

    @property
    @abstractmethod
    def maximum_dec_rate_deg_per_sec(self) -> float:
        ...

    @property
    @abstractmethod
    def is_active(self) -> bool:
        ...

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def apply_rates(self, ra_rate_deg_per_sec: float, dec_rate_deg_per_sec: float) -> TrackingRateCommand:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


    @property
    @abstractmethod
    def position(self) -> Position:
        ...


    @abstractmethod
    def preposition(self, position: Position) -> None:
        ...


    @abstractmethod
    def update(self, elapsed_sec: float) -> None:
        ...