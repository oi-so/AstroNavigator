from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, Qt

from astronavigator.scene.scene import Scene


class Renderer:
    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        self._draw_background(painter, scene, viewport)
        self._draw_objects(painter, scene, viewport)

    def _draw_background(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        painter.fillRect(viewport, Qt.GlobalColor.black)

    def _draw_objects(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        for obj in scene.objects:
            point = scene.sky_camera.projection.project(
                obj.position, 
                scene.sky_camera, 
                viewport.size()
            )

            if point is None: 
                continue

            print("Rendering object:", obj.name, "at screen position:", point)
            painter.setPen(Qt.GlobalColor.white)
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawEllipse(point, 10, 10)