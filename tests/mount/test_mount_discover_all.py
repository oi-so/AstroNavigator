from __future__ import annotations

import time

from astronavigator.mount.mount import ConnectionState, Mount, MountDevice


def test_discover_all_runs_subclasses_in_parallel() -> None:
    sleep_sec = 0.2
    call_intervals: dict[str, tuple[float, float]] = {}

    class SlowMountA(Mount):
        @classmethod
        def discover(cls) -> list[MountDevice]:
            start = time.monotonic()
            time.sleep(sleep_sec)
            call_intervals["A"] = (start, time.monotonic())
            return [MountDevice(driver=cls, name="A", identifier="a")]

        # 以下は本テストでは呼ばれないため最小実装のみ
        @property
        def state(self): return ConnectionState.DISCONNECTED
        def update_status(self): ...
        @property
        def position(self): raise NotImplementedError
        @property
        def driver_name(self): return None
        @property
        def is_tracking(self): return False
        @property
        def is_slewing(self): return False
        def set_tracking(self, tracking): ...
        def connect(self): ...
        def disconnect(self): ...
        def move_axis(self, axis, speed): ...
        def stop_axis(self, axis): ...
        def slew_to(self, position, *, pier_side=None): ...
        def stop(self): ...
        def sync(self, position, *, pier_side=None): ...
        @classmethod
        def create(cls, identifier): raise NotImplementedError

    class SlowMountB(Mount):
        @classmethod
        def discover(cls) -> list[MountDevice]:
            start = time.monotonic()
            time.sleep(sleep_sec)
            call_intervals["B"] = (start, time.monotonic())
            return [MountDevice(driver=cls, name="B", identifier="b")]

        @property
        def state(self): return ConnectionState.DISCONNECTED
        def update_status(self): ...
        @property
        def position(self): raise NotImplementedError
        @property
        def driver_name(self): return None
        @property
        def is_tracking(self): return False
        @property
        def is_slewing(self): return False
        def set_tracking(self, tracking): ...
        def connect(self): ...
        def disconnect(self): ...
        def move_axis(self, axis, speed): ...
        def stop_axis(self, axis): ...
        def slew_to(self, position, *, pier_side=None): ...
        def stop(self): ...
        def sync(self, position, *, pier_side=None): ...
        @classmethod
        def create(cls, identifier): raise NotImplementedError

    devices = Mount.discover_all()

    names = {device.name for device in devices if device.name in ("A", "B")}
    assert names == {"A", "B"}

    # 並列実行されていれば、AとBの実行区間([start, end])が重なるはず。
    # 直列実行だと一方が終わってからもう一方が始まるため重ならない。
    (a_start, a_end) = call_intervals["A"]
    (b_start, b_end) = call_intervals["B"]
    overlap = a_start < b_end and b_start < a_end
    assert overlap, "discover_all() は各サブクラスのdiscover()を並列実行するはず"
