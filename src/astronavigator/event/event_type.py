from __future__ import annotations
from enum import Enum, auto


class EventType(Enum):
    TIME_CHANGED = auto()
    OBSERVER_CHANGED = auto()

    OBJECT_ADDED = auto()
    OBJECT_REMOVED = auto()

    SELECTION_CHANGED = auto()
    FOCUS_CHANGED = auto()

    LAYER_CHANGED = auto()
    
    CAMERA_CHANGED = auto()
    MOUNT_CHANGED = auto()

    CAMERA_MOVED = auto()
    CAMERA_ZOOMED = auto()
    CAMERA_ROTATED = auto()

    SCENE_UPDATED = auto()