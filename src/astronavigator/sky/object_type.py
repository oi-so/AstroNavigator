from __future__ import annotations
from enum import Enum, auto

class ObjectType(Enum):
    STAR = auto()

    SUN = auto()
    PLANET = auto()
    MOON = auto()

    DSO = auto()  # Deep Sky Object

    COMET = auto()
    ASTEROID = auto()

    SATELLITE = auto()