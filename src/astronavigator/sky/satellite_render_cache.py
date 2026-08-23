from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from collections.abc import Mapping

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.sky_object import Satellite, SatelliteBrightness, SatelliteFrameContext, SatelliteObservation


SATELLITE_RENDER_UPDATE_HZ = 20.0



@dataclass(frozen=True, slots=True)
class SatelliteRenderState:
    observation: SatelliteObservation
    brightness: SatelliteBrightness


@dataclass(frozen=True, slots=True)
class SatelliteRenderSnapshot:
    utc: datetime
    observer_key: tuple[float, float, float]
    states: Mapping[str, SatelliteRenderState]


@dataclass(frozen=True, slots=True)
class _SnapshotRequest:
    key: tuple[object, ...]
    time: Time
    observer: Observer
    satellites: tuple[Satellite, ...]


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
        try:
            states: dict[str, SatelliteRenderState] = {}
            frame_contexts: dict[tuple[int, int], SatelliteFrameContext] = {}

            for satellite in self.request.satellites:
                frame_key = (id(satellite.timescale), id(satellite.ephemeris),)

                frame_context = frame_contexts.get(frame_key)

                if frame_context is None:
                    frame_context = (
                        satellite.create_frame_context(self.request.time, self.request.observer,)
                    )
                    frame_contexts[frame_key] = frame_context

                observation = (
                    satellite.calculate_observation(frame_context)
                )

                brightness = (
                    satellite.calculate_brightness(frame_context, observation)
                )

                states[satellite.id] = SatelliteRenderState(observation=observation, brightness=brightness)

            snapshot = SatelliteRenderSnapshot(
                utc=self.request.time.utc,
                observer_key=(
                    self.request.observer.latitude,
                    self.request.observer.longitude,
                    self.request.observer.elevation,
                ),
                states=MappingProxyType(states),
            )

            self.signals.finished.emit(snapshot)

        except Exception as error:
            self.signals.failed.emit(error)




class SatelliteRenderCache(QObject):
    snapshot_changed = Signal(object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)

        self._thread_pool = QThreadPool.globalInstance()

        self._busy = False
        self._pending_request: _SnapshotRequest | None = None
        self._active_task: _SnapshotTask | None = None
        self._latest_request_key: tuple[object, ...] | None = None

        self.snapshot: SatelliteRenderSnapshot | None = None

    def request_update(self, time: Time, observer: Observer, satellites: tuple[Satellite, ...]) -> None:
        time_bucket = int(time.utc.timestamp() * SATELLITE_RENDER_UPDATE_HZ)

        request_key = (
            time_bucket, observer.latitude, observer.longitude, observer.elevation,
            tuple(satellite.id for satellite in satellites),
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
            satellites=satellites,
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
    def _on_finished(self, snapshot: SatelliteRenderSnapshot) -> None:
        self.snapshot = snapshot
        self._busy = False
        self._active_task = None

        self.snapshot_changed.emit(snapshot)
        self._start_pending_request()

    @Slot(object)
    def _on_failed(self, error: Exception) -> None:
        self._busy = False
        self._active_task = None

        print("Satellite snapshot calculation failed:", error,)

        self._start_pending_request()