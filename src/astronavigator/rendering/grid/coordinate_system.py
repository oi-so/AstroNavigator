from enum import Enum, auto


class CoordinateSystem(Enum):
    EQUATORIAL = auto()
    HORIZONTAL = auto()
    GALACTIC = auto()