from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
from statistics import median
import time
from uuid import uuid4

from PySide6.QtCore import QObject, QTimer, Signal

from astronavigator.mount.e_zeus.e_zeus2 import EZeus2
from astronavigator.mount.e_zeus.e_zeus2_protocol import (
    EZeus2_Direction,
    EZeus2_Speed,
)
from astronavigator.mount.mount import Axis
from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.position import Position
from astronavigator.tracking.e_zeus_rate_profile import (
    EZeusRateOption,
    EZeusRateProfile,
)


@dataclass(frozen=True, slots=True)
class EZeusCalibrationStep:
    axis: Axis
    speed: EZeus2_Speed
    direction: EZeus2_Direction
    duration_sec: float

    @property
    def key(
        self,
    ) -> tuple[Axis, EZeus2_Speed, EZeus2_Direction]:
        return (
            self.axis,
            self.speed,
            self.direction,
        )

    @property
    def display_name(self) -> str:
        return (
            f"{self.axis.value} "
            f"{self.speed.name} "
            f"{self.direction.name}"
        )


@dataclass(frozen=True, slots=True)
class _Measurement:
    step: EZeusCalibrationStep
    rate_deg_per_sec: float
    moved_steps: int


CALIBRATION_STEPS = (
    EZeusCalibrationStep(
        Axis.RA,
        EZeus2_Speed.SIDEREAL,
        EZeus2_Direction.FORWARD,
        5.0,
    ),
    EZeusCalibrationStep(
        Axis.RA,
        EZeus2_Speed.SLOW,
        EZeus2_Direction.FORWARD,
        2.0,
    ),
    EZeusCalibrationStep(
        Axis.RA,
        EZeus2_Speed.SLOW,
        EZeus2_Direction.REVERSE,
        2.0,
    ),
    EZeusCalibrationStep(
        Axis.RA,
        EZeus2_Speed.MEDIUM,
        EZeus2_Direction.FORWARD,
        0.5,
    ),
    EZeusCalibrationStep(
        Axis.RA,
        EZeus2_Speed.MEDIUM,
        EZeus2_Direction.REVERSE,
        0.5,
    ),
    EZeusCalibrationStep(
        Axis.RA,
        EZeus2_Speed.FAST,
        EZeus2_Direction.FORWARD,
        0.25,
    ),
    EZeusCalibrationStep(
        Axis.RA,
        EZeus2_Speed.FAST,
        EZeus2_Direction.REVERSE,
        0.25,
    ),
    EZeusCalibrationStep(
        Axis.DEC,
        EZeus2_Speed.SLOW,
        EZeus2_Direction.FORWARD,
        2.0,
    ),
    EZeusCalibrationStep(
        Axis.DEC,
        EZeus2_Speed.SLOW,
        EZeus2_Direction.REVERSE,
        2.0,
    ),
    EZeusCalibrationStep(
        Axis.DEC,
        EZeus2_Speed.MEDIUM,
        EZeus2_Direction.FORWARD,
        0.5,
    ),
    EZeusCalibrationStep(
        Axis.DEC,
        EZeus2_Speed.MEDIUM,
        EZeus2_Direction.REVERSE,
        0.5,
    ),
    EZeusCalibrationStep(
        Axis.DEC,
        EZeus2_Speed.FAST,
        EZeus2_Direction.FORWARD,
        0.25,
    ),
    EZeusCalibrationStep(
        Axis.DEC,
        EZeus2_Speed.FAST,
        EZeus2_Direction.REVERSE,
        0.25,
    ),
)


def calculate_axis_rate_deg_per_sec(
    *,
    delta_steps: int,
    steps_per_revolution: int,
    coordinate_sign: int,
    elapsed_sec: float,
) -> float:
    if steps_per_revolution <= 0:
        raise ValueError(
            "steps_per_revolution must be positive."
        )

    if coordinate_sign not in (-1, 1):
        raise ValueError(
            "coordinate_sign must be -1 or 1."
        )

    if not math.isfinite(elapsed_sec) or elapsed_sec <= 0:
        raise ValueError(
            "elapsed_sec must be positive and finite."
        )

    return (
        delta_steps
        / steps_per_revolution
        * 360.0
        * coordinate_sign
        / elapsed_sec
    )


class EZeusRateCalibrator(QObject):
    progress = Signal(int, int, str)
    measurement_completed = Signal(str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    SETTLE_TIME_MS = 300
    SAMPLE_COUNT = 2
    MINIMUM_MEASURED_STEPS = 3
    RETURN_TIMEOUT_SEC = 30.0
    RETURN_TOLERANCE_DEG = 0.02

    def __init__(
        self,
        mount: EZeus2,
        profile_name: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._mount = mount
        self._profile_name = profile_name

        self._steps = tuple(
            step
            for _ in range(self.SAMPLE_COUNT)
            for step in CALIBRATION_STEPS
        )

        self._index = 0
        self._measurements: list[_Measurement] = []

        self._start_position: Position | None = None
        self._start_pier_side = PierSide.UNKNOWN
        self._was_tracking = False

        self._measurement_start_steps: (
            tuple[int, int] | None
        ) = None
        self._measurement_start_time = 0.0

        self._return_started_time = 0.0
        self._active = False

        self._scheduled_callback = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(
            self._run_scheduled_callback
        )

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def total_steps(self) -> int:
        return len(self._steps)

    def start(self) -> None:
        if self._active:
            raise RuntimeError(
                "Calibration is already active."
            )

        if not self._mount.is_connected:
            raise RuntimeError(
                "E-ZEUS II is not connected."
            )

        if not self._mount.is_synced:
            raise RuntimeError(
                "E-ZEUS IIを先にSyncしてください。"
            )

        if self._mount.is_slewing:
            raise RuntimeError(
                "導入中は校正を開始できません。"
            )

        try:
            self._start_position = self._mount.position
            self._start_pier_side = (
                self._mount.pier_side
            )
            self._was_tracking = (
                self._mount.is_tracking
            )

            self._active = True
            self._mount.stop()

            self._schedule(
                self.SETTLE_TIME_MS,
                self._begin_next_measurement,
            )
        except Exception as error:
            self._handle_failure(error)

    def cancel(self) -> None:
        if not self._active:
            return

        self._timer.stop()
        self._scheduled_callback = None

        try:
            self._mount.stop()
        finally:
            self._active = False
            self.cancelled.emit()

    def _begin_next_measurement(self) -> None:
        if not self._active:
            return

        if self._index >= len(self._steps):
            self._return_to_start()
            return

        step = self._steps[self._index]

        try:
            self._mount.stop_axis(Axis.RA)
            self._mount.stop_axis(Axis.DEC)

            self.progress.emit(
                self._index,
                len(self._steps),
                f"{step.display_name} の測定準備中",
            )

            self._schedule(
                self.SETTLE_TIME_MS,
                self._start_current_measurement,
            )
        except Exception as error:
            self._handle_failure(error)

    def _start_current_measurement(self) -> None:
        if not self._active:
            return

        step = self._steps[self._index]

        try:
            self._measurement_start_steps = (
                self._mount.get_raw_position_steps()
            )

            # DV送信中の移動時間も含めるため、
            # コマンド送信直前を開始時刻とする。
            self._measurement_start_time = (
                time.monotonic()
            )

            self._mount.drive_axis_discrete(
                step.axis,
                step.direction,
                step.speed,
            )

            self.progress.emit(
                self._index,
                len(self._steps),
                f"{step.display_name} を測定中",
            )

            self._schedule(
                round(step.duration_sec * 1000),
                self._finish_current_measurement,
            )
        except Exception as error:
            self._handle_failure(error)

    def _finish_current_measurement(self) -> None:
        if not self._active:
            return

        step = self._steps[self._index]

        try:
            self._mount.stop_axis(step.axis)
            elapsed_sec = (
                time.monotonic()
                - self._measurement_start_time
            )

            end_steps = (
                self._mount.get_raw_position_steps()
            )
            start_steps = self._measurement_start_steps

            if start_steps is None:
                raise RuntimeError(
                    "Measurement start position is missing."
                )

            axis_index = 0 if step.axis is Axis.RA else 1
            steps_per_revolution = (
                self._mount.get_steps_per_revolution(
                    step.axis
                )
            )

            delta_steps = self._step_difference(
                end_steps[axis_index],
                start_steps[axis_index],
                steps_per_revolution,
            )

            rate = calculate_axis_rate_deg_per_sec(
                delta_steps=delta_steps,
                steps_per_revolution=(
                    steps_per_revolution
                ),
                coordinate_sign=(
                    self._mount.get_coordinate_sign(
                        step.axis
                    )
                ),
                elapsed_sec=elapsed_sec,
            )

            self._measurements.append(
                _Measurement(
                    step=step,
                    rate_deg_per_sec=rate,
                    moved_steps=abs(delta_steps),
                )
            )

            self.measurement_completed.emit(
                f"{step.display_name}: "
                f"{rate:+.9f}°/s "
                f"({delta_steps:+d} steps)"
            )

            self._index += 1
            self.progress.emit(
                self._index,
                len(self._steps),
                f"{step.display_name} 完了",
            )

            self._schedule(
                self.SETTLE_TIME_MS,
                self._begin_next_measurement,
            )
        except Exception as error:
            self._handle_failure(error)

    def _return_to_start(self) -> None:
        if not self._active:
            return

        try:
            if (
                self._start_position is None
                or self._start_pier_side
                is PierSide.UNKNOWN
            ):
                raise RuntimeError(
                    "開始位置を復元できません。"
                )

            self.progress.emit(
                len(self._steps),
                len(self._steps),
                "校正開始位置へ戻しています。",
            )

            self._mount.slew_to(
                self._start_position,
                pier_side=self._start_pier_side,
            )

            self._return_started_time = (
                time.monotonic()
            )

            self._schedule(
                self.SETTLE_TIME_MS,
                self._wait_for_return,
            )
        except Exception as error:
            self._handle_failure(error)

    def _wait_for_return(self) -> None:
        if not self._active:
            return

        try:
            current_position = self._mount.position
            target = self._start_position

            if target is None:
                raise RuntimeError(
                    "Return target is missing."
                )

            ra_error = abs(
                (
                    current_position.ra_deg
                    - target.ra_deg
                    + 180.0
                )
                % 360.0
                - 180.0
            )
            dec_error = abs(
                current_position.dec_deg
                - target.dec_deg
            )

            returned = (
                not self._mount.is_slewing
                and ra_error
                <= self.RETURN_TOLERANCE_DEG
                and dec_error
                <= self.RETURN_TOLERANCE_DEG
            )

            if returned:
                self._complete()
                return

            if (
                time.monotonic()
                - self._return_started_time
                > self.RETURN_TIMEOUT_SEC
            ):
                raise TimeoutError(
                    "開始位置への復帰が"
                    "タイムアウトしました。"
                )

            self._schedule(
                self.SETTLE_TIME_MS,
                self._wait_for_return,
            )
        except Exception as error:
            self._handle_failure(error)

    def _complete(self) -> None:
        try:
            self._mount.set_tracking(
                self._was_tracking
            )

            profile = self._create_profile()
            self._active = False
            self.finished.emit(profile)
        except Exception as error:
            self._handle_failure(error)

    def _create_profile(self) -> EZeusRateProfile:
        grouped: dict[
            tuple[
                Axis,
                EZeus2_Speed,
                EZeus2_Direction,
            ],
            list[_Measurement],
        ] = defaultdict(list)

        for measurement in self._measurements:
            grouped[measurement.step.key].append(
                measurement
            )

        options: list[EZeusRateOption] = []

        for key, measurements in grouped.items():
            moved_steps = median(
                measurement.moved_steps
                for measurement in measurements
            )

            # RA SLOW Reverseのような、
            # ほぼ停止する指令は登録しない。
            if moved_steps < self.MINIMUM_MEASURED_STEPS:
                continue

            rate = median(
                measurement.rate_deg_per_sec
                for measurement in measurements
            )

            if math.isclose(
                rate,
                0.0,
                abs_tol=1e-12,
            ):
                continue

            options.append(
                EZeusRateOption(
                    axis=key[0],
                    speed=key[1],
                    drive_direction=key[2],
                    axis_rate_deg_per_sec=rate,
                )
            )

        return EZeusRateProfile(
            profile_id=str(uuid4()),
            name=self._profile_name,
            options=tuple(options),
        )

    def _handle_failure(self, error: Exception) -> None:
        self._timer.stop()
        self._scheduled_callback = None

        try:
            if self._mount.is_connected:
                self._mount.stop()
        except Exception:
            pass

        self._active = False
        self.failed.emit(str(error))

    def _schedule(
        self,
        delay_ms: int,
        callback,
    ) -> None:
        self._scheduled_callback = callback
        self._timer.start(max(0, delay_ms))

    def _run_scheduled_callback(self) -> None:
        callback = self._scheduled_callback
        self._scheduled_callback = None

        if callback is not None:
            callback()

    @staticmethod
    def _step_difference(
        new_steps: int,
        old_steps: int,
        steps_per_revolution: int,
    ) -> int:
        half = steps_per_revolution / 2.0

        return round(
            (
                new_steps
                - old_steps
                + half
            )
            % steps_per_revolution
            - half
        )