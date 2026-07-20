from __future__ import annotations
from enum import Enum, auto

class ObjectType(Enum):
    STAR = auto()
    PLANET = auto()
    MOON = auto()
    SATELLITE = auto()
    COMET = auto()
    ASTEROID = auto()
    DSO = auto()  # Deep Sky Object
    MOUNT = auto()
    CAMERA_FOV = auto()