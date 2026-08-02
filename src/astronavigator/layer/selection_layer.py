from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, Qt

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.scene.scene import Scene

SELECTION_RADIUS = 15


class SelectionLayer(Layer):
    def __init__(self) -> None:
        super().__init__(visible=True, layer_type=LayerType.SELECTION)

    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        selected_obj = scene.selection.selected
        if selected_obj is None:
            return
        
        point = scene.sky_camera.project(
            selected_obj.get_position(),
            viewport.size()
        )

        if point is None:
            return

        color = scene.rendering_settings.color_settings.selection_color
        radius = scene.rendering_settings.selection_radius
        painter.setPen(color)
        painter.setBrush(Qt.GlobalColor.transparent)
        painter.drawEllipse(point, radius, radius)