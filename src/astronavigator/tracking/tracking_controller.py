from __future__ import annotations

from dataclasses import dataclass, replace
import math

from astronavigator.scene.observer import Observer
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import SkyObject
from astronavigator.tracking.mount_tracking import MountTrackingBackend, TrackingRateCommand
from astronavigator.tracking.target_predictor import TargetPrediction, TargetPredictor
from astronavigator.tracking.tracking_adjustment import TrackingAdjustment
from astronavigator.tracking.tracking_config import TrackingConfig
from astronavigator.tracking.tracking_plan import TrackingPlan
from astronavigator.tracking.tracking_safety_policy import TrackingSafetyContext, TrackingSafetyIssueCode, TrackingSafetyPolicy, TrackingSafetyResult
from astronavigator.tracking.tracking_state import TrackingState
from astronavigator.tracking.tracking_time_provider import TrackingTimeProvider


@dataclass(frozen=True, slots=True)
class TrackingControllerSettings:
    position_error_gain_per_sec: float = 0.5
    maximum_position_correction_deg_per_sec: float = 1.0

    def __post_init__(self) -> None:
        values = {
            "position_error_gain_per_sec": (
                self.position_error_gain_per_sec
            ),
            "maximum_position_correction_deg_per_sec": (
                self.maximum_position_correction_deg_per_sec
            ),
        }

        for name, value in values.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
            if value < 0.0:
                raise ValueError(f"{name} must not be negative.")


@dataclass(frozen=True, slots=True)
class TrackingControllerUpdate:
    state: TrackingState
    desired_position: Position | None = None
    prediction: TargetPrediction | None = None
    command: TrackingRateCommand | None = None
    safety_result: TrackingSafetyResult | None = None


class TrackingController:
    def __init__(
        self,
        predictor: TargetPredictor,
        backend: MountTrackingBackend,
        time_provider: TrackingTimeProvider,
        safety_policy: TrackingSafetyPolicy,
        settings: TrackingControllerSettings | None = None,
    ) -> None:
        self._predictor = predictor
        self._backend = backend
        self._time_provider = time_provider
        self._safety_policy = safety_policy
        self._settings = settings or TrackingControllerSettings()

        self._state = TrackingState.IDLE

        self._target: SkyObject | None = None
        self._observer: Observer | None = None
        self._plan: TrackingPlan | None = None
        self._config: TrackingConfig | None = None

        self._adjustment = TrackingAdjustment()

    @property
    def state(self) -> TrackingState:
        return self._state

    @property
    def adjustment(self) -> TrackingAdjustment:
        return self._adjustment

    @property
    def is_active(self) -> bool:
        return self._state in {
            TrackingState.PREPOSITIONING,
            TrackingState.WAITING,
            TrackingState.ACQUIRING,
            TrackingState.TRACKING,
            TrackingState.FLIP_WARNING,
            TrackingState.FLIPPING,
            TrackingState.REACQUIRING,
        }

    @property
    def mount_position(self) -> Position:
        return self._backend.position

    def set_adjustment(self, adjustment: TrackingAdjustment) -> None:
        self._adjustment = adjustment

    def prepare(
        self,
        *,
        target: SkyObject,
        observer: Observer,
        plan: TrackingPlan,
        config: TrackingConfig,
        safety_context: TrackingSafetyContext,
    ) -> TrackingSafetyResult:
        if self.is_active:
            raise RuntimeError("Tracking is already active.")

        if target.id != plan.target_id:
            raise ValueError("The plan target does not match the selected target.")

        snapshot = self._time_provider.get_snapshot()
        checked_context = self._prepare_safety_context(safety_context)

        checked_context = replace(checked_context, run_mode=snapshot.mode, time_rate=snapshot.rate)

        result = self._safety_policy.evaluate_before_start(plan, checked_context)

        if not result.can_start:
            self._state = TrackingState.FAILED
            return result

        self._target = target
        self._observer = observer
        self._plan = plan
        self._config = config

        self._state = TrackingState.PREPOSITIONING
        self._backend.preposition(plan.preposition)
        self._state = TrackingState.WAITING

        return result

    def update(self, elapsed_sec: float, safety_context: TrackingSafetyContext) -> TrackingControllerUpdate:
        self._validate_elapsed(elapsed_sec)

        if self._state in {TrackingState.IDLE, TrackingState.COMPLETED, TrackingState.FAILED}:
            return TrackingControllerUpdate(state=self._state)

        target, observer, plan, config = self._require_prepared_values()
        snapshot = self._time_provider.get_snapshot()

        if plan.end_time_utc is not None and snapshot.utc >= plan.end_time_utc:
            self._complete()
            return TrackingControllerUpdate(state=self._state)

        if self._state is TrackingState.WAITING:
            if snapshot.utc < plan.start_time_utc:
                return TrackingControllerUpdate(self._state)

            self._state = TrackingState.ACQUIRING
            self._backend.start()

        checked_context = self._prepare_safety_context(safety_context)
        checked_context = replace(
            checked_context,
            run_mode=snapshot.mode,
            time_rate=snapshot.rate,
        )

        safety_result = self._safety_policy.evaluate_during_tracking(plan, checked_context)

        if safety_result.should_stop:
            if self._is_normal_altitude_end(safety_result):
                self._complete()
            else:
                self._fail()

            return TrackingControllerUpdate(
                state=self._state,
                safety_result=safety_result,
            )

        prediction = self._predictor.predict_from_provider(
            target=target,
            observer=observer,
            time_provider=self._time_provider,
            prediction_horizon_sec=config.prediction_horizon,
            time_offset_sec=(
                self._adjustment.manual_time_offset_sec
            ),
        )

        desired_position = self._apply_position_adjustment(
            prediction.current_position
        )

        command = self._calculate_and_apply_command(
            prediction=prediction,
            desired_position=desired_position,
            timeline_rate=snapshot.rate,
        )

        self._backend.update(elapsed_sec)

        if self._state is TrackingState.ACQUIRING:
            self._state = TrackingState.TRACKING

        return TrackingControllerUpdate(
            state=self._state,
            desired_position=desired_position,
            prediction=prediction,
            command=command,
            safety_result=safety_result,
        )

    def stop(self) -> None:
        if self._backend.is_active:
            self._backend.stop()

        self._state = TrackingState.COMPLETED

    def reset(self) -> None:
        if self._backend.is_active:
            raise RuntimeError("Cannot reset while backend is active.")

        self._target = None
        self._observer = None
        self._plan = None
        self._config = None
        self._adjustment = TrackingAdjustment()
        self._state = TrackingState.IDLE

    def _calculate_and_apply_command(
        self,
        *,
        prediction: TargetPrediction,
        desired_position: Position,
        timeline_rate: float,
    ) -> TrackingRateCommand:
        current_mount_position = self._backend.position

        ra_error = self._shortest_angle_difference(desired_position.ra_deg, current_mount_position.ra_deg)
        dec_error = desired_position.dec_deg - current_mount_position.dec_deg

        ra_correction = self._calculate_position_correction(ra_error)
        dec_correction = self._calculate_position_correction(dec_error)

        requested_ra_rate = prediction.ra_rate_deg_per_sec * timeline_rate + ra_correction
        requested_dec_rate = prediction.dec_rate_deg_per_sec * timeline_rate + dec_correction

        return self._backend.apply_rates(
            requested_ra_rate,
            requested_dec_rate,
        )

    def _apply_position_adjustment(self, position: Position) -> Position:
        return position.moved(
            delta_ra=self._adjustment.ra_offset_arcsec / 3600.0,
            delta_dec=self._adjustment.dec_offset_arcsec / 3600.0
        )

    def _calculate_position_correction(self, position_error_deg: float) -> float:
        correction = position_error_deg* self._settings.position_error_gain_per_sec
        limit = self._settings.maximum_position_correction_deg_per_sec

        return max(-limit, min(limit, correction))

    def _prepare_safety_context(self, context: TrackingSafetyContext,) -> TrackingSafetyContext:
        return replace(
            context,
            available_ra_rate_deg_per_sec=self._backend.maximum_ra_rate_deg_per_sec,
            available_dec_rate_deg_per_sec=self._backend.maximum_dec_rate_deg_per_sec
        )

    def _complete(self) -> None:
        self._state = TrackingState.STOPPING

        if self._backend.is_active:
            self._backend.stop()

        self._state = TrackingState.COMPLETED

    def _fail(self) -> None:
        if self._backend.is_active:
            self._backend.stop()

        self._state = TrackingState.FAILED

    @staticmethod
    def _is_normal_altitude_end(result: TrackingSafetyResult,) -> bool:
        return any(
            issue.code is TrackingSafetyIssueCode.BELOW_MINIMUM_ALTITUDE
            for issue in result.issues
        )

    @staticmethod
    def _shortest_angle_difference(target_deg: float, current_deg: float) -> float:
        return (target_deg - current_deg + 180.0) % 360.0 - 180.0

    @staticmethod
    def _validate_elapsed(elapsed_sec: float) -> None:
        if not math.isfinite(elapsed_sec):
            raise ValueError("elapsed_sec must be finite.")
        if elapsed_sec < 0.0:
            raise ValueError("elapsed_sec must not be negative.")

    def _require_prepared_values(self) -> tuple[SkyObject, Observer, TrackingPlan, TrackingConfig]:
        if self._target is None or self._observer is None or self._plan is None or self._config is None:
            raise RuntimeError(
                "Tracking controller has not been prepared."
            )

        return (self._target, self._observer, self._plan, self._config)