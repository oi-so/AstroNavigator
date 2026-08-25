from __future__ import annotations

import math

from astronavigator.mount.mount import Axis
from astronavigator.mount.simulator import SimulatorMount
from astronavigator.tracking.mount_tracking import (
    MountTrackingBackend,
    TrackingRateCommand,
)
from astronavigator.sky.position import Position


class SimulatorTrackingBackend(MountTrackingBackend):
    def __init__(self, mount: SimulatorMount) -> None:
        self._mount = mount
        self._is_active = False

    @property
    def maximum_ra_rate_deg_per_sec(self) -> float:
        return (
            self._mount.settings
            .maximum_ra_rate_deg_per_sec
        )

    @property
    def maximum_dec_rate_deg_per_sec(self) -> float:
        return (
            self._mount.settings
            .maximum_dec_rate_deg_per_sec
        )

    @property
    def is_active(self) -> bool:
        return self._is_active

    def start(self) -> None:
        if not self._mount.is_connected:
            raise RuntimeError(
                "Cannot start tracking: mount is not connected."
            )

        if not self._mount.can_move_axis:
            raise RuntimeError(
                "Cannot start tracking: "
                "mount does not support axis movement."
            )

        self._mount.stop_axis(Axis.RA)
        self._mount.stop_axis(Axis.DEC)
        self._mount.set_tracking(True)
        self._is_active = True

    def apply_rates(
        self,
        ra_rate_deg_per_sec: float,
        dec_rate_deg_per_sec: float,
    ) -> TrackingRateCommand:
        if not self._is_active:
            raise RuntimeError(
                "Tracking backend is not active."
            )

        self._validate_rate(
            "ra_rate_deg_per_sec",
            ra_rate_deg_per_sec,
        )
        self._validate_rate(
            "dec_rate_deg_per_sec",
            dec_rate_deg_per_sec,
        )

        applied_ra_rate = self._clamp_rate(
            ra_rate_deg_per_sec,
            self.maximum_ra_rate_deg_per_sec,
        )
        applied_dec_rate = self._clamp_rate(
            dec_rate_deg_per_sec,
            self.maximum_dec_rate_deg_per_sec,
        )

        self._mount.move_axis(
            Axis.RA,
            applied_ra_rate
            / self.maximum_ra_rate_deg_per_sec,
        )
        self._mount.move_axis(
            Axis.DEC,
            applied_dec_rate
            / self.maximum_dec_rate_deg_per_sec,
        )

        return TrackingRateCommand(
            requested_ra_rate_deg_per_sec=(
                ra_rate_deg_per_sec
            ),
            requested_dec_rate_deg_per_sec=(
                dec_rate_deg_per_sec
            ),
            applied_ra_rate_deg_per_sec=applied_ra_rate,
            applied_dec_rate_deg_per_sec=applied_dec_rate,
        )

    def advance(self, elapsed_sec: float) -> None:
        if not self._is_active:
            raise RuntimeError(
                "Tracking backend is not active."
            )

        self._mount.advance(elapsed_sec)

    def stop(self) -> None:
        self._mount.stop_axis(Axis.RA)
        self._mount.stop_axis(Axis.DEC)

        if self._mount.is_connected:
            self._mount.set_tracking(False)

        self._is_active = False

    @staticmethod
    def _clamp_rate(
        requested_rate: float,
        maximum_rate: float,
    ) -> float:
        return max(
            -maximum_rate,
            min(maximum_rate, requested_rate),
        )

    @staticmethod
    def _validate_rate(name: str, value: float) -> None:
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")


    @property
    def position(self) -> Position:
        return self._mount.position

    def preposition(self, position: Position) -> None:
        if not self._mount.is_connected:
            raise RuntimeError(
                "Cannot preposition: mount is not connected."
            )

        self._mount.slew_to(position)

    def update(self, elapsed_sec: float) -> None:
        if not self._is_active:
            return

        self._mount.advance(elapsed_sec)