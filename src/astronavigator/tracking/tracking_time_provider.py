from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import math

from astronavigator.scene.time import Time
from astronavigator.tracking.tracking_state import TrackingRunMode


UtcNowFunction = Callable[[], datetime]
TimeModelGetter = Callable[[], Time]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class TrackingTimeSnapshot:
    utc: datetime
    mode: TrackingRunMode
    rate: float
    is_paused: bool

    def __post_init__(self) -> None:
        if self.utc.tzinfo is None or self.utc.utcoffset() is None:
            raise ValueError("utc must be timezone-aware.")

        if not math.isfinite(self.rate):
            raise ValueError("rate must be finite.")

        object.__setattr__(
            self,
            "utc",
            self.utc.astimezone(timezone.utc),
        )

    @property
    def is_reverse(self) -> bool:
        return self.rate < 0.0

    @property
    def is_stopped(self) -> bool:
        return self.is_paused or self.rate == 0.0


class TrackingTimeProvider(ABC):
    @property
    @abstractmethod
    def mode(self) -> TrackingRunMode:
        ...

    @abstractmethod
    def get_snapshot(self) -> TrackingTimeSnapshot:
        ...

    def get_time(self) -> datetime:
        return self.get_snapshot().utc


class SystemUtcTimeProvider(TrackingTimeProvider):
    def __init__(self, now_function: UtcNowFunction | None = None) -> None:
        self._now_function = now_function or _utc_now

    @property
    def mode(self) -> TrackingRunMode:
        return TrackingRunMode.OBSERVATION

    def get_snapshot(self) -> TrackingTimeSnapshot:
        return TrackingTimeSnapshot(
            utc=self._now_function(),
            mode=self.mode,
            rate=1.0,
            is_paused=False,
        )


class SimulationTimeProvider(TrackingTimeProvider):
    def __init__(self, time_model_getter: TimeModelGetter, mode: TrackingRunMode) -> None:
        if mode not in (TrackingRunMode.REHEARSAL, TrackingRunMode.TEST_TRACKING):
            raise ValueError(
                "mode must be either TrackingRunMode.REHEARSAL or TrackingRunMode.TEST_TRACKING."
            )
        
        self._time_model_getter = time_model_getter
        self._mode = mode

    @property
    def mode(self) -> TrackingRunMode:
        return self._mode

    def get_snapshot(self) -> TrackingTimeSnapshot:
        time_model = self._time_model_getter()

        if not isinstance(time_model, Time):
            raise TypeError(
                "time_model_getter must return a Time instance."
            )

        return TrackingTimeSnapshot(
            utc=time_model.utc,
            mode=self.mode,
            rate=time_model.speed,
            is_paused=time_model.is_paused,
        )