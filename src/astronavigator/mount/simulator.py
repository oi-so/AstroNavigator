from __future__ import annotations

from dataclasses import dataclass
import math

from astronavigator.mount.mount import Axis, ConnectionState, Mount, MountDevice
from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.position import Position


@dataclass(frozen=True, slots=True)
class SimulatorMountSettings:
    maximum_ra_rate_deg_per_sec: float = 4.0
    maximum_dec_rate_deg_per_sec: float = 4.0

    def __post_init__(self) -> None:
        values = {
            "maximum_ra_rate_deg_per_sec": (
                self.maximum_ra_rate_deg_per_sec
            ),
            "maximum_dec_rate_deg_per_sec": (
                self.maximum_dec_rate_deg_per_sec
            ),
        }

        for name, value in values.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
            if value <= 0.0:
                raise ValueError(f"{name} must be positive.")


class SimulatorMount(Mount):
    def __init__(
        self,
        identifier: str = "SIMULATOR_01",
        settings: SimulatorMountSettings | None = None,
    ) -> None:
        self._identifier = identifier
        self._settings = settings or SimulatorMountSettings()

        self._state = ConnectionState.DISCONNECTED
        self._is_tracking = False
        self._position = Position(0.0, 0.0)

        self._ra_rate_deg_per_sec = 0.0
        self._dec_rate_deg_per_sec = 0.0

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def settings(self) -> SimulatorMountSettings:
        return self._settings

    @property
    def position(self) -> Position:
        return Position(
            self._position.ra_deg,
            self._position.dec_deg,
        )

    @property
    def driver_name(self) -> str:
        return "Built-in Mount Simulator"

    @property
    def is_tracking(self) -> bool:
        return self._is_tracking

    @property
    def is_slewing(self) -> bool:
        return (
            self._ra_rate_deg_per_sec != 0.0
            or self._dec_rate_deg_per_sec != 0.0
        )

    @property
    def ra_rate_deg_per_sec(self) -> float:
        return self._ra_rate_deg_per_sec

    @property
    def dec_rate_deg_per_sec(self) -> float:
        return self._dec_rate_deg_per_sec

    def update_status(self) -> None:
        # シミュレーターの状態は各操作で即時更新されるため、
        # 外部装置から読み直す処理は不要。
        return

    def connect(self) -> None:
        if self._state is ConnectionState.CONNECTED:
            return

        self._state = ConnectionState.CONNECTING
        self._state = ConnectionState.CONNECTED

    def disconnect(self) -> None:
        self._stop_all_motion()
        self._is_tracking = False
        self._state = ConnectionState.DISCONNECTED

    def set_tracking(self, tracking: bool) -> None:
        self._require_connected()
        self._is_tracking = tracking

    def sync(self, position: Position, *, pier_side: PierSide | None = None) -> None:
        self._require_connected()
        self._position = position.normalized()

    def slew_to(self, position: Position, *, pier_side: PierSide | None = None) -> None:
        self._require_connected()
        self._position = position.normalized()

    def move_axis(self, axis: Axis, speed: float) -> None:
        self._require_connected()

        if not math.isfinite(speed):
            raise ValueError("speed must be finite.")

        if not -1.0 <= speed <= 1.0:
            raise ValueError(
                "speed must be between -1.0 and 1.0."
            )

        if axis is Axis.RA:
            self._ra_rate_deg_per_sec = (
                speed
                * self._settings.maximum_ra_rate_deg_per_sec
            )
        elif axis is Axis.DEC:
            self._dec_rate_deg_per_sec = (
                speed
                * self._settings.maximum_dec_rate_deg_per_sec
            )
        else:
            raise ValueError(f"Unsupported axis: {axis}")

    def stop_axis(self, axis: Axis) -> None:
        if axis is Axis.RA:
            self._ra_rate_deg_per_sec = 0.0
        elif axis is Axis.DEC:
            self._dec_rate_deg_per_sec = 0.0
        else:
            raise ValueError(f"Unsupported axis: {axis}")

    def stop(self) -> None:
        self._stop_all_motion()
        self._is_tracking = False

    def advance(self, elapsed_sec: float) -> None:
        """指定した経過時間だけシミュレーターを進める。"""

        self._require_connected()

        if not math.isfinite(elapsed_sec):
            raise ValueError("elapsed_sec must be finite.")

        if elapsed_sec < 0.0:
            raise ValueError("elapsed_sec must not be negative.")

        if elapsed_sec == 0.0:
            return

        self._position = self._position.moved(
            delta_ra=self._ra_rate_deg_per_sec * elapsed_sec,
            delta_dec=self._dec_rate_deg_per_sec * elapsed_sec,
        )

    def _stop_all_motion(self) -> None:
        self._ra_rate_deg_per_sec = 0.0
        self._dec_rate_deg_per_sec = 0.0

    def _require_connected(self) -> None:
        if not self.is_connected:
            raise RuntimeError(
                "Simulator mount is not connected."
            )

    @property
    def can_sync(self) -> bool:
        return True

    @property
    def can_slew(self) -> bool:
        return True

    @property
    def can_home(self) -> bool:
        return False

    @property
    def can_move_axis(self) -> bool:
        return True

    @classmethod
    def discover(cls) -> list[MountDevice]:
        return [
            MountDevice(
                driver=cls,
                name="Mount Simulator",
                identifier="SIMULATOR_01",
                description=(
                    "実機なしで軸速度追尾をテストする仮想望遠鏡"
                ),
            )
        ]

    @classmethod
    def create(cls, identifier: str) -> Mount:
        return cls(identifier)