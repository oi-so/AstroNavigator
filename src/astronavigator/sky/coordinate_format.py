from enum import Enum, auto


class RightAscensionFormat(Enum):
    DEGREE = auto()
    HMS = auto()


class DeclinationFormat(Enum):
    DEGREE = auto()
    DMS = auto()