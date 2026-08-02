from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.grid_renderer import GridRenderer
from astronavigator.scene.scene import Scene

class GridLayer(Layer):
    def __init__(self) -> None:
        super().__init__(visible=True, layer_type=LayerType.GRID)

        self.renderer = GridRenderer()

    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        if not self.visible:
            return

        self.renderer.render(painter, scene, viewport)