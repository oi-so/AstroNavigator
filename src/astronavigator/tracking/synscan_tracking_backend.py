from __future__ import annotations

import math

from astronavigator.mount.mount import Axis
from astronavigator.mount.synscan.synscan_mount import SynScanMount
from astronavigator.tracking.mount_tracking import MountTrackingBackend, TrackingRateCommand
from astronavigator.sky.position import Position


class SynScanTrackingBackend(MountTrackingBackend):
    """SynScan Pro (ASCOM MoveAxis) を利用した動的天体追尾バックエンド。

    SynScanMount.move_axis() は度/秒単位の連続レートをそのまま
    MoveAxisコマンドへ渡す実装になっているため、EZeusTrackingBackendの
    ような離散レートの選択・変調は不要で、SimulatorTrackingBackendと
    同様に要求レートをそのまま(最大値でクランプして)送るだけでよい。
    """

    def __init__(self, mount: SynScanMount) -> None:
        self._mount = mount
        self._is_active = False

    @property
    def maximum_ra_rate_deg_per_sec(self) -> float:
        return self._mount.settings.maximum_ra_rate_deg_per_sec

    @property
    def maximum_dec_rate_deg_per_sec(self) -> float:
        return self._mount.settings.maximum_dec_rate_deg_per_sec

    @property
    def is_active(self) -> bool:
        return self._is_active

    def start(self) -> None:
        self._require_ready()

        if not self._mount.can_move_axis:
            raise RuntimeError(
                "The connected SynScan mount does not support MoveAxis-based tracking."
            )

        self._mount.stop_axis(Axis.RA)
        self._mount.stop_axis(Axis.DEC)
        self._is_active = True

    def apply_rates(self, ra_rate_deg_per_sec: float, dec_rate_deg_per_sec: float) -> TrackingRateCommand:
        if not self._is_active:
            raise RuntimeError("Cannot apply rates when tracking is not active.")

        self._validate_rate("ra_rate_deg_per_sec", ra_rate_deg_per_sec)
        self._validate_rate("dec_rate_deg_per_sec", dec_rate_deg_per_sec)

        applied_ra_rate = self._clamp_rate(ra_rate_deg_per_sec, self.maximum_ra_rate_deg_per_sec)
        applied_dec_rate = self._clamp_rate(dec_rate_deg_per_sec, self.maximum_dec_rate_deg_per_sec)

        self._mount.move_axis(Axis.RA, applied_ra_rate)
        self._mount.move_axis(Axis.DEC, applied_dec_rate)

        return TrackingRateCommand(
            requested_ra_rate_deg_per_sec=ra_rate_deg_per_sec,
            requested_dec_rate_deg_per_sec=dec_rate_deg_per_sec,
            applied_ra_rate_deg_per_sec=applied_ra_rate,
            applied_dec_rate_deg_per_sec=applied_dec_rate,
            ra_rate_limited=not math.isclose(ra_rate_deg_per_sec, applied_ra_rate, abs_tol=1e-12),
            dec_rate_limited=not math.isclose(dec_rate_deg_per_sec, applied_dec_rate, abs_tol=1e-12),
        )

    def stop(self) -> None:
        if self._mount.is_connected:
            self._mount.stop_axis(Axis.RA)
            self._mount.stop_axis(Axis.DEC)

        self._is_active = False

    @property
    def position(self) -> Position:
        return self._mount.position

    def preposition(self, position: Position) -> None:
        self._require_ready()
        self._mount.slew_to(position)

    def update(self, elapsed_sec: float) -> None:
        if not math.isfinite(elapsed_sec) or elapsed_sec < 0.0:
            raise ValueError("elapsed_sec must be a non-negative finite number.")

        if not self._mount.is_connected:
            return

        self._mount.update_status()

    @property
    def preposition_complete(self) -> bool:
        if not self._mount.is_connected:
            return False

        return not self._mount.is_slewing

    def _require_ready(self) -> None:
        if not self._mount.is_connected:
            raise RuntimeError("Mount is not connected.")

        if not self._mount.is_synced:
            raise RuntimeError("Mount is not synced. Perform alignment/sync before tracking.")

    @staticmethod
    def _clamp_rate(requested_rate: float, maximum_rate: float) -> float:
        return max(-maximum_rate, min(maximum_rate, requested_rate))

    @staticmethod
    def _validate_rate(name: str, value: float) -> None:
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")
