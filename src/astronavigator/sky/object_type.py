from __future__ import annotations
from enum import Enum, auto

class ObjectType(Enum):
    STAR = auto()

    PLANET = auto()
    MOON = auto()

    DSO = auto()  # Deep Sky Object

    COMET = auto()
    ASTEROID = auto()

    SATELLITE = auto()
    
    MOUNT = auto()
    CAMERA_FOV = auto()