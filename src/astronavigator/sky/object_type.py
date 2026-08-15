from __future__ import annotations
from enum import Enum

class ObjectType(Enum):
    STAR = "Star"

    SUN = "Sun"
    MOON = "Moon"
    PLANET = "Planet"

    DSO = "DeepSkyObject"  # Deep Sky Object

    COMET = "Comet"
    ASTEROID = "Asteroid"

    SATELLITE = "Satellite"