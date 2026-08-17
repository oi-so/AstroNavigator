from astronavigator.rendering.label_layout import LabelLayout
from astronavigator.rendering.projection.projection import Projection
from astronavigator.scene.scene import Scene


from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter


from dataclasses import dataclass, field
from typing import Generic, TypeVar



P = TypeVar("P")
C = TypeVar("C")


@dataclass(slots=True)
class RendererContext(Generic[P, C]):
    painter: QPainter
    scene: Scene
    viewport: QRect
    projection: Projection[P, C]
    projection_context: C
    label_layout: LabelLayout = field(default_factory=LabelLayout)