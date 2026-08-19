from __future__ import annotations

from dataclasses import dataclass
import math

from astronavigator.mount.e_zeus.e_zeus2 import EZeus2
from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2_Direction, EZeus2_Speed
from astronavigator.mount.mount import Axis
from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.position import Position
from astronavigator.tracking.e_zeus_rate_profile import EZeusRateOption,EZeusRateProfile
from astronavigator.tracking.mount_tracking import MountTrackingBackend, TrackingRateCommand


SIDEREAL_DAY_SECONDS = 86164.0905
SIDEREAL_RATE_DEG_PER_SEC = 360.0 / SIDEREAL_DAY_SECONDS


@dataclass(slots=True)
class _AxisModulationState:
    remaining_displacement_deg: float = 0.0
    last_direction: int = 0

    active_speed: EZeus2_Speed = EZeus2_Speed.STOP
    active_drive_direction: EZeus2_Direction | None = None


class EZeusTrackingBackend(MountTrackingBackend):
    def __init__(self, mount: EZeus2, rate_profile: EZeusRateProfile, control_interval_sec: float) -> None:
        if not math.isfinite(control_interval_sec) or control_interval_sec <= 0.0:
            raise ValueError("control_interval_sec must be a positive finite number.")

        self._mount = mount
        self._rate_profile = rate_profile
        self._control_interval_sec = control_interval_sec

        self._is_active = False
        self._ra_state = _AxisModulationState()
        self._dec_state = _AxisModulationState()


    @property
    def position(self) -> Position:
        return self._mount.position

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def maximum_ra_rate_deg_per_sec(self) -> float:
        sky_rates = [option.axis_rate_deg_per_sec + SIDEREAL_RATE_DEG_PER_SEC for option in self._rate_profile.options_for_axis(Axis.RA)]
        sky_rates.append(SIDEREAL_RATE_DEG_PER_SEC)
        return max(abs(rate) for rate in sky_rates)


    @property
    def maximum_dec_rate_deg_per_sec(self) -> float:
        return max(abs(option.axis_rate_deg_per_sec) for option in self._rate_profile.options_for_axis(Axis.DEC))

    def preposition(self, position: Position) -> None:
        self._require_ready()
        if self._mount.pier_side is PierSide.UNKNOWN:
            raise RuntimeError("Cannot preposition when pier side is unknown.")

        self._mount.slew_to(position, pier_side=self._mount.pier_side)


    def start(self) -> None:
        self._require_ready()
        self._mount.set_tracking(False)
        self._reset_status()
        self._is_active = True


    def apply_rates(self, ra_rate_deg_per_sec: float, dec_rate_deg_per_sec: float) -> TrackingRateCommand:
        if not self._is_active:
            raise RuntimeError("Cannot apply rates when tracking is not active.")

        self._validate_rate("ra_rate_deg_per_sec", ra_rate_deg_per_sec)
        self._validate_rate("dec_rate_deg_per_sec", dec_rate_deg_per_sec)

        requested_ra_axis_rate = ra_rate_deg_per_sec - SIDEREAL_RATE_DEG_PER_SEC
        requested_dec_axis_rate = -dec_rate_deg_per_sec if self._mount.pier_side is PierSide.WEST else dec_rate_deg_per_sec

        ra_option, applied_ra_rate, ra_limited = self._select_option(
            axis=Axis.RA, requested_axis_rate=requested_ra_axis_rate, state=self._ra_state
        )
        dec_option, applied_dec_rate, dec_limited = self._select_option(
            axis=Axis.DEC, requested_axis_rate=requested_dec_axis_rate, state=self._dec_state
        )

        self._apply_option(Axis.RA, ra_option, self._ra_state)
        self._apply_option(Axis.DEC, dec_option, self._dec_state)

        applied_ra_sky_rate = applied_ra_rate + SIDEREAL_RATE_DEG_PER_SEC
        applied_dec_sky_rate = -applied_dec_rate if self._mount.pier_side is PierSide.WEST else applied_dec_rate

        return TrackingRateCommand(
            requested_ra_rate_deg_per_sec=ra_rate_deg_per_sec,
            requested_dec_rate_deg_per_sec=dec_rate_deg_per_sec,
            applied_ra_rate_deg_per_sec=applied_ra_sky_rate,
            applied_dec_rate_deg_per_sec=applied_dec_sky_rate,
            ra_rate_limited=ra_limited,
            dec_rate_limited=dec_limited,
        )


    def update(self, elapsed_sec: float) -> None:
        if not math.isfinite(elapsed_sec) or elapsed_sec < 0.0:
            raise ValueError("elapsed_sec must be a non-negative finite number.")


    def stop(self) -> None:
        if self._mount.is_connected:
            self._mount.stop_axis(Axis.RA)
            self._mount.stop_axis(Axis.DEC)
            self._mount.set_tracking(False)

        self._is_active = False
        self._reset_status()


    def _select_option(self, *, axis: Axis, requested_axis_rate: float, state: _AxisModulationState) -> tuple[EZeusRateOption | None, float, bool]:
        if math.isclose(requested_axis_rate, 0.0, abs_tol=1e-6):
            state.remaining_displacement_deg = 0.0
            state.last_direction = 0
            return None, 0.0, False

        direction = 1 if requested_axis_rate > 0.0 else -1
        if direction != state.last_direction:
            state.remaining_displacement_deg = 0.0
            state.last_direction = direction

        options = self._rate_profile.options_for_direction(axis, direction)

        if not options:
            raise RuntimeError(f"No rate options available for axis {axis} in direction {direction}.")

        max_rate = max(abs(option.axis_rate_deg_per_sec) for option in options)
        limited = abs(requested_axis_rate) > max_rate
        effective_rate = max(-max_rate, min(requested_axis_rate, max_rate))

        desired_displacement = effective_rate * self._control_interval_sec + state.remaining_displacement_deg

        candidates: list[tuple[EZeusRateOption | None, float]] = [(None, 0.0)]
        candidates.extend((option, option.axis_rate_deg_per_sec) for option in options)

        selected_option, selected_rate = min(candidates, key=lambda candidate: abs(desired_displacement - candidate[1] * self._control_interval_sec))

        state.remaining_displacement_deg = desired_displacement - selected_rate * self._control_interval_sec

        return selected_option, selected_rate, limited



    def _apply_option(self, axis: Axis, option: EZeusRateOption | None, state: _AxisModulationState) -> None:
        speed = EZeus2_Speed.STOP if option is None else option.speed
        direction = 0 if option is None else option.drive_direction

        if state.active_speed is speed and state.active_drive_direction is direction:
            return

        if option is None:
            self._mount.stop_axis(axis)
        else:
            self._mount.drive_axis_discrete(axis, option.drive_direction, option.speed)

        state.active_speed = speed
        state.active_drive_direction = direction


    def _require_ready(self) -> None:
        if not self._mount.is_connected:
            raise RuntimeError("Mount is not connected.")

        if self._mount.pier_side is PierSide.UNKNOWN or not self._mount.is_synced:
            raise RuntimeError("Mount is not ready for tracking (pier side unknown or not synced).")

    def _reset_status(self) -> None:
        self._ra_state = _AxisModulationState()
        self._dec_state = _AxisModulationState()


    @staticmethod
    def _validate_rate(name: str, rate: float) -> None:
        if not math.isfinite(rate):
            raise ValueError(f"{name} must be a finite number.")