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


COMET_RENDER_UPDATE_HZ = 2.0
COMET_RENDER_BATCH_SIZE = 32


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
    comets_to_update: tuple[Comet, ...]
    active_comet_ids: tuple[str, ...]


class _TaskSignals(QObject):
    finished = Signal(object)
    failed = Signal(object)


@dataclass(frozen=True, slots=True)
class _TaskResult:
    utc: datetime
    observer_key: tuple[float, float, float]
    active_comet_ids: tuple[str, ...]
    states: Mapping[str, CometRenderState]
    calculation_seconds: float


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

            for comet in self.request.comets_to_update:
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

            result = _TaskResult(
                utc=self.request.time.utc,
                observer_key=(
                    self.request.observer.latitude,
                    self.request.observer.longitude,
                    self.request.observer.elevation,
                ),
                active_comet_ids=self.request.active_comet_ids,
                states=MappingProxyType(states),
                calculation_seconds=perf_counter() - started_at,
            )
            self.signals.finished.emit(result)

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
        self._next_batch_start_index = 0
        self._state_cache: dict[str, CometRenderState] = {}

        self.snapshot: CometRenderSnapshot | None = None

    def request_update(self, time: Time, observer: Observer, comets: tuple[Comet, ...]) -> None:
        if self._busy:
            return

        time_bucket = int(time.utc.timestamp() * COMET_RENDER_UPDATE_HZ)
        comet_ids = tuple(comet.id for comet in comets)
        active_comets = tuple(comet for comet in comets if comet.is_active(time))
        active_comet_ids = tuple(comet.id for comet in active_comets)

        comets_to_update = self._select_update_batch(active_comets)

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
            comets_to_update=comets_to_update,
            active_comet_ids=active_comet_ids,
        )
        self._pending_request = request

        if not self._busy:
            self._start_pending_request()

    def _select_update_batch(self, comets: tuple[Comet, ...]) -> tuple[Comet, ...]:
        count = len(comets)
        if count == 0:
            self._next_batch_start_index = 0
            return ()

        if count <= COMET_RENDER_BATCH_SIZE:
            self._next_batch_start_index = 0
            return comets

        start = self._next_batch_start_index % count
        end = start + COMET_RENDER_BATCH_SIZE
        if end <= count:
            batch = comets[start:end]
        else:
            batch = comets[start:] + comets[: end - count]

        self._next_batch_start_index = end % count
        return batch

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
    def _on_finished(self, result: _TaskResult) -> None:
        active_id_set = set(result.active_comet_ids)
        stale_ids = [comet_id for comet_id in self._state_cache if comet_id not in active_id_set]
        for comet_id in stale_ids:
            del self._state_cache[comet_id]

        self._state_cache.update(result.states)

        snapshot = CometRenderSnapshot(
            utc=result.utc,
            observer_key=result.observer_key,
            states=MappingProxyType(dict(self._state_cache)),
            calculation_seconds=result.calculation_seconds,
        )
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
