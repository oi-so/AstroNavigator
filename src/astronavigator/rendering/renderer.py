from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, Qt

from astronavigator.layer.constellation_layer import ConstellationLayer
from astronavigator.layer.grid_layer import GridLayer
from astronavigator.layer.layer_manager import LayerManager
from astronavigator.layer.object_layer import ObjectLayer
from astronavigator.scene.scene import Scene


SELECTION_RADIUS = 15



class Renderer:
    def __init__(self) -> None:
        self.layer_manager = LayerManager()

        self.layer_manager.add_layer(GridLayer())
        self.layer_manager.add_layer(ConstellationLayer())
        self.layer_manager.add_layer(ObjectLayer())


    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        self._draw_background(painter, scene, viewport)

        self.layer_manager.render(painter, scene, viewport)
        self._draw_selection(painter, scene, viewport)


    def _draw_background(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        painter.fillRect(viewport, Qt.GlobalColor.black)

        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)

    def _draw_selection(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        selected_obj = scene.selection.selected
        if selected_obj is None:
            return
        
        point = scene.sky_camera.project(
            selected_obj.get_position(),
            viewport.size()
        )

        if point is None:
            return
        
        painter.setPen(Qt.GlobalColor.red)
        painter.setBrush(Qt.GlobalColor.transparent)
        painter.drawEllipse(point, SELECTION_RADIUS, SELECTION_RADIUS)
