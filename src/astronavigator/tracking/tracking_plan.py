from __future__ import annotations


from dataclasses import dataclass
from datetime import datetime, timezone
import math


from astronavigator.mount.mount import Axis
from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.position import Position
from astronavigator.tracking.tracking_state import TrackingPlanStatus


def _normalize_utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware.")

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class RateLimitWarning:
    axis: Axis
    required_rate_deg_per_sec: float
    available_rate_deg_per_sec: float


    def __post_init__(self) -> None:
        values = {
            "required_rate_dec_per_sec": self.required_rate_deg_per_sec,
            "available_rate_dec_per_sec": self.available_rate_deg_per_sec,
        }

        for name, value in values.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value}")

        if self.required_rate_deg_per_sec <= self.available_rate_deg_per_sec:
            raise ValueError(
                f"required_rate_dec_per_sec must be greater than available_rate_dec_per_sec, "
                f"got {self.required_rate_deg_per_sec} <= {self.available_rate_deg_per_sec}"
            )

    @property
    def shortage_deg_per_sec(self) -> float:
        return self.required_rate_deg_per_sec - self.available_rate_deg_per_sec


@dataclass(frozen=True, slots=True)
class TrackingPlan:
    target_id: str
    status: TrackingPlanStatus

    start_time_utc: datetime
    end_time_utc: datetime | None

    initial_pier_side: PierSide
    preposition: Position

    maximum_required_ra_rate_deg_per_sec: float
    maximum_required_dec_rate_deg_per_sec: float

    requires_meridian_flip: bool
    meridian_flip_time_utc: datetime | None

    rate_profile_id: str | None

    rate_limit_warnings: tuple[RateLimitWarning, ...] = ()
    warnings: tuple[str, ...] = ()
    blocked_reason: str | None = None


    def __post_init__(self) -> None:
        if not self.target_id.strip():
            raise ValueError(f"target_id must be a non-empty string, got '{self.target_id}'")

        if self.rate_profile_id is not None and not self.rate_profile_id.strip():
            raise ValueError(f"rate_profile_id must be a non-empty string if specified, got '{self.rate_profile_id}'")

        start_time = _normalize_utc(self.start_time_utc, "start_time_utc")
        object.__setattr__(self, "start_time_utc", start_time)

        if self.end_time_utc is not None:
            end_time = _normalize_utc(self.end_time_utc, "end_time_utc")
            object.__setattr__(self, "end_time_utc", end_time)

            if end_time < start_time:
                raise ValueError(f"end_time_utc must be >= start_time_utc, got {end_time} < {start_time}")

        if self.meridian_flip_time_utc is not None:
            flip_time = _normalize_utc(self.meridian_flip_time_utc, "meridian_flip_time_utc")
            object.__setattr__(self, "meridian_flip_time_utc", flip_time)

            if flip_time < start_time:
                raise ValueError(f"meridian_flip_time_utc must be >= start_time_utc, got {flip_time} < {start_time}")

            if self.end_time_utc is not None and flip_time > self.end_time_utc:
                raise ValueError(f"meridian_flip_time_utc must be <= end_time_utc, got {flip_time} > {self.end_time_utc}")

        self._validate_rates()

        object.__setattr__(self,  "rate_limit_warnings", tuple(self.rate_limit_warnings))
        object.__setattr__(self,  "warnings", tuple(self.warnings))

        if self.requires_meridian_flip and self.meridian_flip_time_utc is None and self.status is not TrackingPlanStatus.BLOCKED:
            raise ValueError("requires_meridian_flip is True and status is BLOCKED, but meridian_flip_time_utc is None")

        if not self.requires_meridian_flip and self.meridian_flip_time_utc is not None:
            raise ValueError("requires_meridian_flip is False, but meridian_flip_time_utc is not None")

        if self.status is TrackingPlanStatus.BLOCKED and not self.blocked_reason:
            raise ValueError("status is BLOCKED, but blocked_reason is not specified")

        if self.status is not TrackingPlanStatus.BLOCKED and self.blocked_reason:
            raise ValueError("status is not BLOCKED, but blocked_reason is specified")

        if self.status is TrackingPlanStatus.READY and self.rate_limit_warnings:
            raise ValueError("status is READY, but rate_limit_warnings is not empty")


    def _validate_rates(self) -> None:
        rates = {
            "maximum_required_ra_rate_deg_per_sec": self.maximum_required_ra_rate_deg_per_sec,
            "maximum_required_dec_rate_deg_per_sec": self.maximum_required_dec_rate_deg_per_sec,
        }

        for name, value in rates.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value}")