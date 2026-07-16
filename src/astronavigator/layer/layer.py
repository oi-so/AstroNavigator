from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass


class LayerType(Enum):
    Stars = auto()
    Planets = auto()
    Grid = auto()
    Labels = auto()
    MilkyWay = auto()
    SATELLITE = auto()
    MOUNT = auto()



@dataclass(slots=True)
class Layer:
    visible: bool
    priority: int
    layer_type: LayerType
