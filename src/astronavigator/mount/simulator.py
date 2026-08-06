from __future__ import annotations

import time
from astronavigator.mount.mount import Axis, ConnectionState, Mount, MountDevice
from astronavigator.sky.position import Position


# AIさんが作ってくれました

class SimulatorMount(Mount):
    """ダミー動作を行うシミュレーター用マウント"""

    def __init__(self, identifier: str = "SIM_01") -> None:
        self._identifier = identifier
        self._state = ConnectionState.DISCONNECTED
        self._is_tracking = False
        self._position = Position(0.0, 0.0)  # 初期位置 (RA: 0.0°, Dec: 0.0°)
        self._driver_name = "Built-in Mount Simulator"

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def is_tracking(self) -> bool:
        return self._is_tracking

    @property
    def driver_name(self) -> str:
        return self._driver_name

    @property
    def position(self) -> Position:
        # 本来は時間経過や手動操作に応じて座標を推移させる処理をここに入れることも可能
        return self._position

    @property
    def is_slewing(self) -> bool:
        return False

    def connect(self) -> None:
        self._state = ConnectionState.CONNECTING
        # 接続の疑似ウェイト（0.2秒）
        time.sleep(0.2)
        self._state = ConnectionState.CONNECTED

    def disconnect(self) -> None:
        self._state = ConnectionState.DISCONNECTED

    def set_tracking(self, tracking: bool) -> None:
        self._is_tracking = tracking

    def sync(self, position: Position) -> None:
        """指定した位置に同期（現在位置を上書き）"""
        self._position = position

    def slew_to(self, position: Position) -> None:
        """指定位置へ導入（シミュレーターなので即座に移動完了）"""
        self._position = position

    def move_axis(self, axis: Axis, speed: float) -> None:
        # 手動移動の疑似処理
        pass

    def stop_axis(self, axis: Axis) -> None:
        pass

    def stop(self) -> None:
        pass

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

    # ----------------------------------------------------
    # discover & create
    # ----------------------------------------------------
    @classmethod
    def discover(cls) -> list[MountDevice]:
        """
        ハードウェアの状態に関わらず、常にシミュレーターデバイスを1つ返す
        """
        return [
            MountDevice(
                driver=cls,
                name="Mount Simulator",
                identifier="SIMULATOR_01",
                description="仮想望遠鏡（実機がなくてもテスト可能）",
            )
        ]

    @classmethod
    def create(cls, identifier: str) -> Mount:
        mount = cls(identifier)
        return mount