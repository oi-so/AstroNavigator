from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from astronavigator.mount.slew_path import PierSide
from astronavigator.scene.observer import Observer
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import SkyObject
from astronavigator.tracking.target_horizontal_position_calculator import TargetHorizontalPositionCalculator

from astronavigator.tracking.target_predictor import TargetPredictor
from astronavigator.tracking.tracking_config import TrackingConfig
from astronavigator.tracking.tracking_plan import TrackingPlan
from astronavigator.tracking.tracking_state import TrackingPlanStatus
from astronavigator.tracking.tracking_time_provider import TrackingTimeProvider


@dataclass(frozen=True, slots=True)
class TrackingPlannerSettings:
    search_horizon_sec: float = 24.0 * 60.0 * 60.0
    coarse_search_interval_sec: float = 30.0
    crossing_precision_sec: float = 0.1

    motion_sample_interval_sec: float = 1.0
    max_motion_samples: int = 100

    def __post_init__(self) -> None:
        numeric_values = {
            "search_horizon_sec": self.search_horizon_sec,
            "coarse_search_interval_sec": self.coarse_search_interval_sec,
            "crossing_precision_sec": self.crossing_precision_sec,
            "motion_sample_interval_sec": self.motion_sample_interval_sec,
        }

        for name, value in numeric_values.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a number.")
            if value <= 0.0:
                raise ValueError(f"{name} must be positive.")

        if self.max_motion_samples < 2:
            raise ValueError("max_motion_samples must be at least 2.")


class TrackingPlanner:
    def __init__(
        self,
        predictor: TargetPredictor,
        horizontal_calculator: TargetHorizontalPositionCalculator,
        settings: TrackingPlannerSettings | None = None
    ) -> None:
        self._predictor = predictor
        self._horizontal_calculator = horizontal_calculator
        self._settings = settings or TrackingPlannerSettings()

    def create_plan(self, target: SkyObject, observer: Observer, time_provider: TrackingTimeProvider, config: TrackingConfig) -> TrackingPlan:
        snapshot = time_provider.get_snapshot()
        planning_start_utc = snapshot.utc
        search_end_utc = planning_start_utc + timedelta(seconds=self._settings.search_horizon_sec)

        current_position = self._get_position(target, observer, planning_start_utc, config.prediction_horizon)

        current_altitude = self._get_altitude(current_position, observer, planning_start_utc)


        warnings: list[str] = []

        if current_altitude >= config.entry_altitude_deg:
            tracking_start_utc = planning_start_utc
            warnings.append("対象天体はすでに開始高度以上にあります。")
        else:
            tracking_start_utc = self._find_crossing(
                target, observer, planning_start_utc, search_end_utc, config.entry_altitude_deg, rising=True, predictor_horizon_sec=config.prediction_horizon
            )

        if tracking_start_utc is None:
            return self._create_blocked_plan(
                target, planning_start_utc, current_position, config, reason="指定された時間内に対象天体が追尾開始高度に達しませんでした。",
            )

        preposition = self._get_position(target, observer, tracking_start_utc, config.prediction_horizon)

        tracking_end_limit_utc = search_end_utc

        if config.max_session_sec is not None:
            max_session_end = tracking_start_utc + timedelta(seconds=config.max_session_sec)
            tracking_end_limit_utc = min(tracking_end_limit_utc, max_session_end)


        tracking_end_utc = self._find_crossing(
            target, observer, tracking_start_utc, tracking_end_limit_utc, config.exit_altitude_deg, rising=False, predictor_horizon_sec=config.prediction_horizon, require_initially_above=True
        )

        if tracking_end_utc is None:
            if config.max_session_sec is not None:
                tracking_end_utc = tracking_end_limit_utc
                warnings.append("最大追尾時間で追尾を終了します。")
            else:
                warnings.append("指定された時間内に対象天体が追尾終了高度を下回りませんでした。")

        rate_sample_end_utc = tracking_end_utc or search_end_utc

        max_ra_rate, max_dec_rate, = self._calculate_max_rates(target, observer, tracking_start_utc, rate_sample_end_utc, config.prediction_horizon)


        return TrackingPlan(
            target_id=target.id,
            status=TrackingPlanStatus.READY,
            start_time_utc=tracking_start_utc,
            end_time_utc=tracking_end_utc,
            initial_pier_side=PierSide.UNKNOWN,
            preposition=preposition,
            maximum_required_ra_rate_deg_per_sec=(max_ra_rate),
            maximum_required_dec_rate_deg_per_sec=(max_dec_rate),
            requires_meridian_flip=False,
            meridian_flip_time_utc=None,
            rate_profile_id=config.rate_profile_id,
            warnings=tuple(warnings),
        )

    def _find_crossing(self, target: SkyObject, observer: Observer, search_start_utc: datetime, search_end_utc: datetime, altitude_deg: float, rising: bool, predictor_horizon_sec: float, *, require_initially_above: bool = False) -> datetime | None:
        previous_time = search_start_utc
        previous_position = self._get_position(target, observer, previous_time, predictor_horizon_sec)
        previous_altitude = self._get_altitude(previous_position, observer, previous_time)

        has_been_above = previous_altitude > altitude_deg


        while previous_time < search_end_utc:
            current_time = min(previous_time + timedelta(seconds=self._settings.coarse_search_interval_sec), search_end_utc)
            current_position = self._get_position(target, observer, current_time, predictor_horizon_sec)
            current_altitude = self._get_altitude(current_position, observer, current_time)

            if current_altitude > altitude_deg:
                has_been_above = True

            if rising:
                crossed = previous_altitude < altitude_deg <= current_altitude
            else:
                crossed = previous_altitude > altitude_deg >= current_altitude
                if require_initially_above:
                    crossed = crossed and has_been_above

            if crossed:
                return self._refine_crossing(target, observer, previous_time, current_time, altitude_deg, rising, predictor_horizon_sec)

            if current_time == previous_time:
                break

            previous_time = current_time
            previous_altitude = current_altitude

        return None

    def _refine_crossing(self, target: SkyObject, observer: Observer, start_time: datetime, end_time: datetime, altitude_deg: float, rising: bool, predictor_horizon_sec: float) -> datetime:
        while (end_time - start_time).total_seconds() > self._settings.crossing_precision_sec:
            mid_time = start_time + (end_time - start_time) / 2
            mid_position = self._get_position(target, observer, mid_time, predictor_horizon_sec)
            mid_altitude = self._get_altitude(mid_position, observer, mid_time)

            if rising:
                if mid_altitude < altitude_deg:
                    start_time = mid_time
                else:
                    end_time = mid_time
            else:
                if mid_altitude > altitude_deg:
                    start_time = mid_time
                else:
                    end_time = mid_time

        return end_time

    def _calculate_max_rates(self, target: SkyObject, observer: Observer, start_time: datetime, end_time: datetime, predictor_horizon_sec: float) -> tuple[float, float]:
        duration_sec = (end_time - start_time).total_seconds()

        if duration_sec <= 0.0:
            prediction = self._predictor.predict(target, observer, start_time, predictor_horizon_sec)
            return abs(prediction.ra_rate_deg_per_sec), abs(prediction.dec_rate_deg_per_sec)

        sample_interval_sec = max(self._settings.motion_sample_interval_sec, duration_sec / (self._settings.max_motion_samples - 1))
        sample_count = min(self._settings.max_motion_samples, math.ceil(duration_sec / sample_interval_sec) + 1)

        max_ra_rate = 0.0
        max_dec_rate = 0.0

        for index in range(sample_count):
            sample_time = min(start_time + timedelta(seconds=index * sample_interval_sec), end_time)
            prediction = self._predictor.predict(target, observer, sample_time, predictor_horizon_sec)
            max_ra_rate = max(max_ra_rate, abs(prediction.ra_rate_deg_per_sec))
            max_dec_rate = max(max_dec_rate, abs(prediction.dec_rate_deg_per_sec))

        return max_ra_rate, max_dec_rate


    def _get_position(self, target: SkyObject, observer: Observer, time_utc: datetime, predictor_horizon_sec: float) -> Position:
        prediction = self._predictor.predict(target, observer, time_utc, predictor_horizon_sec)
        return prediction.current_position



    def _get_altitude(self, position: Position, observer: Observer, time_utc: datetime) -> float:
        horizontal_position = self._horizontal_calculator.calculate(position, time_utc, observer)
        return horizontal_position.altitude_deg


    def _create_blocked_plan(self, target: SkyObject, current_time_utc: datetime, current_position: Position, config: TrackingConfig, reason: str) -> TrackingPlan:
        return TrackingPlan(
            target_id=target.id,
            status=TrackingPlanStatus.BLOCKED,
            start_time_utc=current_time_utc,
            end_time_utc=None,
            initial_pier_side=PierSide.UNKNOWN,
            preposition=current_position,
            maximum_required_ra_rate_deg_per_sec=0.0,
            maximum_required_dec_rate_deg_per_sec=0.0,
            requires_meridian_flip=False,
            meridian_flip_time_utc=None,
            rate_profile_id=config.rate_profile_id,
            warnings=(reason,),
            blocked_reason=reason
        )