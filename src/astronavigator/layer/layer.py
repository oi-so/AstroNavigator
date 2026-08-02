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
    GRID = auto()
    CONSTELLATION = auto()
    LABELS = auto()

    OBJECTS = auto()
    SELECTION = auto()

    MILKY_WAY = auto()
    MOUNT = auto()



@dataclass(slots=True)
class Layer(ABC):
    visible: bool
    layer_type: LayerType

    @abstractmethod
    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        ...