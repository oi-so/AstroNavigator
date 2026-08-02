from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from astronavigator.scene.scene import Scene


class LayerType(Enum):
    Stars = auto()
    Planets = auto()
    Grid = auto()
    Labels = auto()
    MilkyWay = auto()
    Constellation = auto()
    SATELLITE = auto()
    MOUNT = auto()



@dataclass(slots=True)
class Layer(ABC):
    visible: bool
    layer_type: LayerType

    @abstractmethod
    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        pass