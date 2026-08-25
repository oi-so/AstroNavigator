from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from types import MappingProxyType

import numpy as np
from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot
from sgp4.api import SGP4_ERRORS, SatrecArray, accelerated, jday
from skyfield.sgp4lib import TEME

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.sky_object import Satellite, SatelliteBrightness, SatelliteObservation


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
    calculation_seconds: float


@dataclass(frozen=True, slots=True)
class _SnapshotRequest:
    key: tuple[object, ...]
    time: Time
    observer: Observer
    satellites: tuple[Satellite, ...]
    satrec_array: SatrecArray


class _TaskSignals(QObject):
    finished = Signal(object)
    failed = Signal(object)


class _SnapshotTask(QRunnable):
    def __init__(self, request: _SnapshotRequest):
        super().__init__()
        self.request = request
        self.signals = _TaskSignals()

    # @profile
    @Slot()
    def run(self) -> None:
        started_at = perf_counter()

        try:
            states: dict[str, SatelliteRenderState] = {}
            satellites = self.request.satellites

            if not satellites:
                snapshot = SatelliteRenderSnapshot(
                    utc=self.request.time.utc,
                    observer_key=(
                        self.request.observer.latitude,
                        self.request.observer.longitude,
                        self.request.observer.elevation,
                    ),
                    states=MappingProxyType(states),
                    calculation_seconds=(
                        perf_counter() - started_at
                    ),
                )
                self.signals.finished.emit(snapshot)
                return

            first_satellite = satellites[0]

            frame_context = (
                first_satellite.create_frame_context(
                    self.request.time,
                    self.request.observer,
                )
            )

            utc = self.request.time.utc

            julian_day, fraction = jday(
                utc.year,
                utc.month,
                utc.day,
                utc.hour,
                utc.minute,
                utc.second + utc.microsecond / 1_000_000.0,
            )

            julian_days = np.array([julian_day], dtype=np.float64)
            fractions = np.array([fraction], dtype=np.float64)

            errors, teme_positions, _ = (
                self.request.satrec_array.sgp4(julian_days, fractions)
            )

            # SatrecArrayの結果:
            # (衛星数, 時刻数, xyz)
            teme_positions = teme_positions[:, 0, :]
            errors = errors[:, 0]

            # SkyfieldのEarthSatellite.at()と同じ
            # TEME -> GCRS変換
            teme_to_gcrs = np.asarray(
                TEME.rotation_at(frame_context.skyfield_time),
                dtype=np.float64,
            ).T

            gcrs_positions = np.einsum(
                "ij,nj->ni",
                teme_to_gcrs,
                teme_positions,
                optimize=True,
            )

            for index, satellite in enumerate(satellites):
                error_code = int(errors[index])

                if error_code != 0:
                    message = SGP4_ERRORS.get(
                        error_code,
                        f"SGP4 error {error_code}",
                    )
                    print(
                        f"Satellite calculation failed: "
                        f"{satellite.name}: {message}"
                    )
                    continue

                vector = gcrs_positions[index]

                satellite_vector = (
                    float(vector[0]),
                    float(vector[1]),
                    float(vector[2]),
                )

                observation = (
                    satellite.calculate_observation_from_vector(
                        frame_context,
                        satellite_vector,
                    )
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
                calculation_seconds=perf_counter() - started_at,
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

        self._satrec_model_key: tuple[int, ...] = ()
        self._satrec_array: SatrecArray | None = None

        self.snapshot: SatelliteRenderSnapshot | None = None

        if not accelerated:
            print(
                "Warning: sgp4 C++ acceleration is disabled. "
                "Satellite rendering may be slow."
            )

    def request_update(self, time: Time, observer: Observer, satellites: tuple[Satellite, ...]) -> None:
        time_bucket = int(time.utc.timestamp() * SATELLITE_RENDER_UPDATE_HZ)

        satellite_ids = tuple(satellite.id for satellite in satellites)

        request_key = (
            time_bucket,
            observer.latitude,
            observer.longitude,
            observer.elevation,
            satellite_ids,
        )

        if request_key == self._latest_request_key:
            return

        self._latest_request_key = request_key

        satrec_array = self._get_satrec_array(satellites)

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
            satrec_array=satrec_array,
        )

        self._pending_request = request

        if not self._busy:
            self._start_pending_request()

    def _get_satrec_array(self, satellites: tuple[Satellite, ...]) -> SatrecArray:
        model_key = tuple(id(satellite.model.model) for satellite in satellites)

        if self._satrec_array is not None and model_key == self._satrec_model_key:
            return self._satrec_array

        satrec_array = SatrecArray([satellite.model.model for satellite in satellites])

        self._satrec_model_key = model_key
        self._satrec_array = satrec_array

        return satrec_array

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
        QTimer.singleShot(0, self._start_pending_request)

    @Slot(object)
    def _on_failed(self, error: Exception) -> None:
        self._busy = False
        self._active_task = None

        print("Satellite snapshot calculation failed:", repr(error),)

        QTimer.singleShot(0, self._start_pending_request)

