from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from types import MappingProxyType

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Comet


COMET_RENDER_UPDATE_HZ = 10.0
COMET_RENDER_BATCH_SIZE = 4
COMET_VISIBLE_REFRESH_SECONDS = 30.0
COMET_BACKGROUND_REFRESH_SECONDS = 300.0
COMET_VISIBILITY_MARGIN_MAG = 1.0


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


class _TaskSignals(QObject):
    finished = Signal(object)
    failed = Signal(object)


@dataclass(frozen=True, slots=True)
class _TaskResult:
    key: tuple[object, ...]
    utc: datetime
    observer_key: tuple[float, float, float]
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
            failed_comets: list[str] = []

            for comet in self.request.comets_to_update:
                try:
                    position = comet.get_position(
                        self.request.time, self.request.observer
                    )
                    magnitude = comet.get_magnitude(
                        self.request.time, self.request.observer
                    )
                except Exception as error:
                    if len(failed_comets) < 5:
                        failed_comets.append(f"{comet.name}: {repr(error)}")
                    continue

                states[comet.id] = CometRenderState(
                    position=position,
                    magnitude=magnitude,
                )

            if failed_comets:
                # print("Comet calculation failed:", "; ".join(failed_comets))
                pass

            result = _TaskResult(
                key=self.request.key,
                utc=self.request.time.utc,
                observer_key=(
                    self.request.observer.latitude,
                    self.request.observer.longitude,
                    self.request.observer.elevation,
                ),
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
        self._next_priority_batch_start_index = 0
        self._next_background_batch_start_index = 0
        self._state_cache: dict[str, CometRenderState] = {}

        self._updated_at: dict[str, datetime] = {}
        self._context_key: tuple[object, ...] | None = None
        self._generation = 0
        self._next_update_at = 0.0
        self.snapshot: CometRenderSnapshot | None = None

    def request_update(
        self,
        time: Time,
        observer: Observer,
        comets: tuple[Comet, ...],
        limiting_magnitude: float,
        selected_id: str | None = None,
        focus_id: str | None = None,
    ) -> None:
        context_key = (observer.latitude, observer.longitude, observer.elevation)
        context_key += (time.revision,)
        if context_key != self._context_key:
            self._context_key = context_key
            self._generation += 1
            self._state_cache.clear()
            self._updated_at.clear()
            self.snapshot = None
            self.snapshot_changed.emit(None)

        # 実時間で休止期間を設け、早送り中も計算スレッドがGUIのCPUを占有しない。
        if self._busy or perf_counter() < self._next_update_at:
            return
        self._next_update_at = perf_counter() + 1.0 / COMET_RENDER_UPDATE_HZ
        comets_to_update = self._select_update_batch(
            comets, limiting_magnitude, time, selected_id, focus_id
        )
        if not comets_to_update:
            return
        request = _SnapshotRequest(
            key=(self._generation,),
            time=Time(utc=time.utc, speed=time.speed, is_paused=time.is_paused),
            observer=Observer(
                latitude=observer.latitude,
                longitude=observer.longitude,
                elevation=observer.elevation,
                timezone=observer.timezone,
            ),
            comets_to_update=comets_to_update,
        )
        self._pending_request = request
        self._start_pending_request()

    def _select_update_batch(
        self,
        comets: tuple[Comet, ...],
        limiting_magnitude: float,
        time: Time,
        selected_id: str | None = None,
        focus_id: str | None = None,
    ) -> tuple[Comet, ...]:
        priority: list[Comet] = []
        background: list[Comet] = []
        selected: list[Comet] = []
        for comet in comets:
            state = self._state_cache.get(comet.id)
            is_visible = state is not None and state.magnitude.is_visible(
                limiting_magnitude + COMET_VISIBILITY_MARGIN_MAG
            )
            interval = (
                COMET_VISIBLE_REFRESH_SECONDS
                if is_visible
                else COMET_BACKGROUND_REFRESH_SECONDS
            )
            if comet.id in (selected_id, focus_id):
                interval = 1.0
            updated_at = self._updated_at.get(comet.id)
            if (
                updated_at is not None
                and abs((time.utc - updated_at).total_seconds()) < interval
            ):
                continue
            if comet.id in (selected_id, focus_id):
                selected.append(comet)
            elif is_visible:
                priority.append(comet)
            else:
                background.append(comet)
        # 明るい彗星が多い場合でも、未計算・暗い彗星の順番を必ず確保する。
        priority_capacity = COMET_RENDER_BATCH_SIZE - len(selected) - bool(background)
        selected.extend(
            self._take_round_robin(tuple(priority), priority_capacity, is_priority=True)
        )
        selected.extend(
            self._take_round_robin(
                tuple(background),
                COMET_RENDER_BATCH_SIZE - len(selected),
                is_priority=False,
            )
        )
        return tuple(selected)

    def _take_round_robin(
        self, comets: tuple[Comet, ...], take: int, *, is_priority: bool
    ) -> tuple[Comet, ...]:
        if take <= 0 or not comets:
            return ()

        count = len(comets)
        if count <= take:
            if is_priority:
                self._next_priority_batch_start_index = 0
            else:
                self._next_background_batch_start_index = 0
            return comets

        start = (
            self._next_priority_batch_start_index
            if is_priority
            else self._next_background_batch_start_index
        ) % count
        end = start + take
        if end <= count:
            batch = comets[start:end]
        else:
            batch = comets[start:] + comets[: end - count]

        if is_priority:
            self._next_priority_batch_start_index = end % count
        else:
            self._next_background_batch_start_index = end % count
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
        self._busy = False
        task = self._active_task
        self._active_task = None
        # 計算時間の9倍を休止し、定常時の計算負荷を抑える。
        self._next_update_at = perf_counter() + max(
            1.0 / COMET_RENDER_UPDATE_HZ, result.calculation_seconds * 9.0
        )
        # 古い観測地点や時刻への要求が完了しても、新しいSceneへ混在させない。
        if result.key != (self._generation,):
            return
        if task is not None:
            for comet in task.request.comets_to_update:
                self._updated_at[comet.id] = result.utc
                self._state_cache.pop(comet.id, None)

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

    @Slot(object)
    def _on_failed(self, error: Exception) -> None:
        self._busy = False
        self._active_task = None

        print("Comet snapshot calculation failed:", repr(error))
