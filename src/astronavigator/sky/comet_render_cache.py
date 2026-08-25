from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from types import MappingProxyType

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Comet


COMET_RENDER_UPDATE_HZ = 1.0


@dataclass(frozen=True, slots=True)
class CometRenderState:
    position: Position
    magnitude: Magnitude


@dataclass(frozen=True, slots=True)
class CometRenderSnapshot:
    utc: datetime
    observer_key: tuple[float, float, float]
    states: Mapping[str, CometRenderState]
    calculation_seconds: float


@dataclass(frozen=True, slots=True)
class _SnapshotRequest:
    key: tuple[object, ...]
    time: Time
    observer: Observer
    comets: tuple[Comet, ...]


class _TaskSignals(QObject):
    finished = Signal(object)
    failed = Signal(object)


class _SnapshotTask(QRunnable):
    def __init__(self, request: _SnapshotRequest):
        super().__init__()
        self.request = request
        self.signals = _TaskSignals()

    @Slot()
    def run(self) -> None:
        started_at = perf_counter()

        try:
            states: dict[str, CometRenderState] = {}

            for comet in self.request.comets:
                if not comet.is_active(self.request.time):
                    continue

                try:
                    position = comet.get_position(self.request.time, self.request.observer)
                    magnitude = comet.get_magnitude(self.request.time, self.request.observer)
                except Exception as error:
                    print(f"Comet calculation failed: {comet.name}: {repr(error)}")
                    continue

                states[comet.id] = CometRenderState(
                    position=position,
                    magnitude=magnitude,
                )

            snapshot = CometRenderSnapshot(
                utc=self.request.time.utc,
                observer_key=(
                    self.request.observer.latitude,
                    self.request.observer.longitude,
                    self.request.observer.elevation,
                ),
                states=MappingProxyType(states),
                calculation_seconds=perf_counter() - started_at,
            )
            self.signals.finished.emit(snapshot)

        except Exception as error:
            self.signals.failed.emit(error)


class CometRenderCache(QObject):
    snapshot_changed = Signal(object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)

        self._thread_pool = QThreadPool.globalInstance()

        self._busy = False
        self._pending_request: _SnapshotRequest | None = None
        self._active_task: _SnapshotTask | None = None
        self._latest_request_key: tuple[object, ...] | None = None

        self.snapshot: CometRenderSnapshot | None = None

    def request_update(self, time: Time, observer: Observer, comets: tuple[Comet, ...]) -> None:
        time_bucket = int(time.utc.timestamp() * COMET_RENDER_UPDATE_HZ)
        comet_ids = tuple(comet.id for comet in comets)

        request_key = (
            time_bucket,
            observer.latitude,
            observer.longitude,
            observer.elevation,
            comet_ids,
        )
        if request_key == self._latest_request_key:
            return

        self._latest_request_key = request_key

        request = _SnapshotRequest(
            key=request_key,
            time=Time(
                utc=time.utc,
                speed=time.speed,
                is_paused=time.is_paused,
            ),
            observer=Observer(
                latitude=observer.latitude,
                longitude=observer.longitude,
                elevation=observer.elevation,
                timezone=observer.timezone,
            ),
            comets=comets,
        )
        self._pending_request = request

        if not self._busy:
            self._start_pending_request()

    def _start_pending_request(self) -> None:
        request = self._pending_request
        if request is None:
            return

        self._pending_request = None
        self._busy = True

        task = _SnapshotTask(request)
        task.signals.finished.connect(self._on_finished)
        task.signals.failed.connect(self._on_failed)

        self._active_task = task
        self._thread_pool.start(task)

    @Slot(object)
    def _on_finished(self, snapshot: CometRenderSnapshot) -> None:
        self.snapshot = snapshot
        self._busy = False
        self._active_task = None

        self.snapshot_changed.emit(snapshot)
        QTimer.singleShot(0, self._start_pending_request)

    @Slot(object)
    def _on_failed(self, error: Exception) -> None:
        self._busy = False
        self._active_task = None

        print("Comet snapshot calculation failed:", repr(error))

        QTimer.singleShot(0, self._start_pending_request)
