from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass

from astronavigator.rendering.render_context import RendererContext


class LayerType(Enum):
    GRID = auto()
    CONSTELLATION = auto()
    LABELS = auto()

    OBJECTS = auto()
    HORIZON = auto()
    SELECTION = auto()

    MILKY_WAY = auto()
    MOUNT = auto()



@dataclass(slots=True)
class Layer(ABC):
    visible: bool
    layer_type: LayerType

    @abstractmethod
    def render(self, context: RendererContext) -> None:
        ...