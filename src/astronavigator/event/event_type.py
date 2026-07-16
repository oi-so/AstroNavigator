from __future__ import annotations
from enum import Enum, auto


class EventType(Enum):
    TIME_CHANGED = auto()
    OBSERVER_CHANGED = auto()
    SCENE_UPDATED = auto()
    LAYER_CHANGED = auto()
    SELECTION_CHANGED = auto()
    CAMERA_CHANGED = auto()
    MOUNT_CHANGED = auto()