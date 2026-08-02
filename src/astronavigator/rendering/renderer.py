from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, Qt

from astronavigator.layer.constellation_layer import ConstellationLayer
from astronavigator.layer.grid_layer import GridLayer
from astronavigator.layer.layer_manager import LayerManager
from astronavigator.layer.object_layer import ObjectLayer
from astronavigator.rendering.selection_layer import SelectionLayer
from astronavigator.scene.scene import Scene


class Renderer:
    def __init__(self) -> None:
        self.layer_manager = LayerManager()

        self.layer_manager.add_layer(GridLayer())
        self.layer_manager.add_layer(ConstellationLayer())
        self.layer_manager.add_layer(ObjectLayer())
        self.layer_manager.add_layer(SelectionLayer())


    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        self._draw_background(painter, scene, viewport)

        self.layer_manager.render(painter, scene, viewport)


    def _draw_background(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        painter.fillRect(viewport, Qt.GlobalColor.black)

        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
