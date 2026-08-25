from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import SkyObject
from astronavigator.tracking.tracking_time_provider import TrackingTimeProvider


def _normalize_utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware.")

    return value.astimezone(timezone.utc)



def _shortest_ra_difference(target_ra_deg: float, source_ra_deg: float) -> float:
    return (target_ra_deg - source_ra_deg + 180.0) % 360.0 - 180.0


def _angular_separation_deg(first: Position, second: Position) -> float:
    first_ra = math.radians(first.ra_deg)
    first_dec = math.radians(first.dec_deg)
    second_ra = math.radians(second.ra_deg)
    second_dec = math.radians(second.dec_deg)

    cos = math.sin(first_dec) * math.sin(second_dec) + math.cos(first_dec) * math.cos(second_dec) * math.cos(first_ra - second_ra)
    cos = max(-1.0, min(1.0, cos))

    return math.degrees(math.acos(cos))


@dataclass(frozen=True, slots=True)
class TargetPrediction:
    target_id: str
    target_name: str

    current_time_utc: datetime
    future_time_utc: datetime

    current_position: Position
    future_position: Position

    ra_rate_deg_per_sec: float
    dec_rate_deg_per_sec: float
    angular_rate_deg_per_sec: float


    def __post_init__(self) -> None:
        current_time_utc = _normalize_utc(self.current_time_utc, "current_time_utc")
        future_time_utc = _normalize_utc(self.future_time_utc, "future_time_utc")

        if future_time_utc <= current_time_utc:
            raise ValueError("future_time_utc must be after current_time_utc.")

        object.__setattr__(self, "current_time_utc", current_time_utc)
        object.__setattr__(self, "future_time_utc", future_time_utc)

        rates = {
            "ra_rate_deg_per_sec": self.ra_rate_deg_per_sec,
            "dec_rate_deg_per_sec": self.dec_rate_deg_per_sec,
            "angular_rate_deg_per_sec": self.angular_rate_deg_per_sec,
        }

        for name, value in rates.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a number.")

        if self.angular_rate_deg_per_sec < 0.0:
            raise ValueError("angular_rate_deg_per_sec must be non-negative.")


    @property
    def duration_sec(self) -> float:
        return (self.future_time_utc - self.current_time_utc).total_seconds()


class TargetPredictor:
    def predict(self, target: SkyObject, observer: Observer, current_time_utc: datetime, prediction_horizon_sec: float) -> TargetPrediction:
        if not math.isfinite(prediction_horizon_sec) or prediction_horizon_sec <= 0.0:
            raise ValueError("prediction_horizon_sec must be a positive finite number.")

        current_time_utc = _normalize_utc(current_time_utc, "current_time_utc")
        future_time_utc = current_time_utc + timedelta(seconds=prediction_horizon_sec)

        current_position = self._get_position(target, observer, current_time_utc)
        future_position = self._get_position(target, observer, future_time_utc)

        delta_ra_deg = _shortest_ra_difference(future_position.ra_deg, current_position.ra_deg)
        delta_dec_deg = future_position.dec_deg - current_position.dec_deg
        angular_difference_deg = _angular_separation_deg(current_position, future_position)

        return TargetPrediction(
            target_id=target.id,
            target_name=target.name,
            current_time_utc=current_time_utc,
            future_time_utc=future_time_utc,
            current_position=current_position,
            future_position=future_position,
            ra_rate_deg_per_sec=delta_ra_deg / prediction_horizon_sec,
            dec_rate_deg_per_sec=delta_dec_deg / prediction_horizon_sec,
            angular_rate_deg_per_sec=angular_difference_deg / prediction_horizon_sec,
        )


    def predict_from_provider(self, target: SkyObject, observer: Observer, time_provider: TrackingTimeProvider, prediction_horizon_sec: float, *, time_offset_sec: float = 0.0) -> TargetPrediction:
        if not math.isfinite(time_offset_sec):
            raise ValueError("time_offset_sec must be a finite number.")

        snapshot = time_provider.get_snapshot()
        prediction_time = snapshot.utc + timedelta(seconds=time_offset_sec)
        return self.predict(target, observer, prediction_time, prediction_horizon_sec)


    def _get_position(self, target: SkyObject, observer: Observer, time_utc: datetime) -> Position:
        time_model = Time(utc=time_utc)
        position = target.get_position(time_model, observer)
        return position.normalized()