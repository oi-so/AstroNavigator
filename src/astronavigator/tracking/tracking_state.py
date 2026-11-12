from __future__ import annotations

from enum import Enum, auto



class TrackingPlanStatus(Enum):
    READY = auto()
    DEGRADED = auto()
    BLOCKED = auto()


class TrackingRunMode(Enum):
    OBSERVATION = auto()
    REHEARSAL = auto()
    TEST_TRACKING = auto()


class MeridianStrategy(Enum):
    AVOID_DURING_TRACKING = auto()
    AUTO_FLIP = auto()
    STOP_BEFORE_LIMIT = auto()


class TrackingState(Enum):
    IDLE = auto()
    PLANNING = auto()
    PREPOSITIONING = auto()
    WAITING = auto()
    ACQUIRING = auto()
    TRACKING = auto()
    FLIP_WARNING = auto()
    FLIPPING = auto()
    REACQUIRING = auto()
    STOPPING = auto()
    COMPLETED = auto()
    FAILED = auto()