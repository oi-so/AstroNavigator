from __future__ import annotations

from datetime import datetime, timezone
import math

from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer
from astronavigator.catalog.parser.skyfield_parser import SkyfieldContext
from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import SkyObject
from astronavigator.tracking.target_predictor import TargetPrediction, TargetPredictor


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

    cosine = math.sin(first_dec) * math.sin(second_dec) + math.cos(first_dec) * math.cos(second_dec) * math.cos(first_ra - second_ra)
    cosine = max(-1.0, min(1.0, cosine))

    return math.degrees(math.acos(cosine))


class ReplayCoordinateMapper:
    def __init__(self, *, context: SkyfieldContext, observer: Observer, simulation_anchor_utc: datetime, real_anchor_utc: datetime) -> None:
        self._context = context
        self._observer = observer
        self._simulation_anchor_utc = _normalize_utc(
            simulation_anchor_utc,
            "simulation_anchor_utc",
        )
        self._real_anchor_utc = _normalize_utc(
            real_anchor_utc,
            "real_anchor_utc",
        )

    def real_time_for(self, simulation_time_utc: datetime) -> datetime:
        simulation_time_utc = _normalize_utc(
            simulation_time_utc,
            "simulation_time_utc",
        )

        elapsed = simulation_time_utc - self._simulation_anchor_utc
        return self._real_anchor_utc + elapsed

    def simulation_time_for(self, real_time_utc: datetime) -> datetime:
        real_time_utc = _normalize_utc(
            real_time_utc,
            "real_time_utc",
        )

        elapsed = real_time_utc - self._real_anchor_utc
        return self._simulation_anchor_utc + elapsed

    def simulation_to_real(self, position: Position, simulation_time_utc: datetime) -> Position:
        simulation_time_utc = _normalize_utc(
            simulation_time_utc,
            "simulation_time_utc",
        )
        real_time_utc = self.real_time_for(simulation_time_utc)

        horizontal = (
            CoordinateTransformer.equatorial_to_horizontal_at(
                position=position,
                time=Time(utc=simulation_time_utc),
                observer=self._observer,
                context=self._context,
            )
        )

        return CoordinateTransformer.horizontal_to_equatorial(
            position=horizontal,
            time=Time(utc=real_time_utc),
            observer=self._observer,
            context=self._context,
        )

    def real_to_simulation(self, position: Position, real_time_utc: datetime) -> Position:
        real_time_utc = _normalize_utc(
            real_time_utc,
            "real_time_utc",
        )
        simulation_time_utc = self.simulation_time_for(real_time_utc)

        horizontal = (
            CoordinateTransformer.equatorial_to_horizontal_at(
                position=position,
                time=Time(utc=real_time_utc),
                observer=self._observer,
                context=self._context,
            )
        )

        return CoordinateTransformer.horizontal_to_equatorial(
            position=horizontal,
            time=Time(utc=simulation_time_utc),
            observer=self._observer,
            context=self._context,
        )


class ReplayedTargetPredictor(TargetPredictor):
    def __init__(self, mapper: ReplayCoordinateMapper, source_predictor: TargetPredictor | None = None) -> None:
        self._mapper = mapper
        self._source_predictor = (
            source_predictor or TargetPredictor()
        )

    def predict(
        self,
        target: SkyObject,
        observer: Observer,
        current_time_utc: datetime,
        prediction_horizon_sec: float,
    ) -> TargetPrediction:
        source = self._source_predictor.predict(
            target=target,
            observer=observer,
            current_time_utc=current_time_utc,
            prediction_horizon_sec=prediction_horizon_sec,
        )

        current_position = (
            self._mapper.simulation_to_real(
                source.current_position,
                source.current_time_utc,
            )
        )
        future_position = (
            self._mapper.simulation_to_real(
                source.future_position,
                source.future_time_utc,
            )
        )

        duration_sec = source.duration_sec

        delta_ra_deg = _shortest_ra_difference(future_position.ra_deg, current_position.ra_deg)
        delta_dec_deg = future_position.dec_deg - current_position.dec_deg
        angular_difference_deg = _angular_separation_deg(current_position,future_position)

        return TargetPrediction(
            target_id=source.target_id,
            target_name=source.target_name,
            current_time_utc=source.current_time_utc,
            future_time_utc=source.future_time_utc,
            current_position=current_position,
            future_position=future_position,
            ra_rate_deg_per_sec=delta_ra_deg / duration_sec,
            dec_rate_deg_per_sec=delta_dec_deg / duration_sec,
            angular_rate_deg_per_sec=angular_difference_deg / duration_sec
        )