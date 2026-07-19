from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, Qt

from astronavigator.camera.sky_camera import SkyCamera
from astronavigator.scene.scene import Scene
from astronavigator.sky.sky_object import SkyObject


class Renderer:
    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        self._draw_background(painter, scene, viewport)
        self._draw_objects(painter, scene, viewport)

    def _draw_background(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        painter.fillRect(viewport, Qt.GlobalColor.black)

    def _draw_objects(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        
        for obj in scene.objects:
            self._draw_object(obj, painter, scene.sky_camera, viewport)

    def _draw_object(self, obj: SkyObject, painter: QPainter, camera: SkyCamera, viewport: QRect) -> None:
        point = camera.project(
                obj.get_position(), 
                viewport.size()
            )

        if point is None: 
            return

        painter.drawEllipse(point, 10, 10)