from __future__ import annotations

from PySide6.QtCore import QPointF, QRect
from PySide6.QtGui import QPainter, Qt

from astronavigator.camera.sky_camera import SkyCamera
from astronavigator.scene.scene import Scene
from astronavigator.sky.sky_object import SkyObject, Star, Moon, Satellite, Comet, DeepSkyObject
from astronavigator.sky.magnitude import Magnitude


SELECTION_RADIUS = 15
LABEL_OFFSET = QPointF(5, -5)


class Renderer:
    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        self._draw_background(painter, scene, viewport)
        self._draw_objects(painter, scene, viewport)
        self._draw_selection(painter, scene, viewport)
        self._draw_labels(painter, scene, viewport)

    def _draw_background(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        painter.fillRect(viewport, Qt.GlobalColor.black)

    def _draw_objects(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        for obj in scene.objects:
            self._draw_object(obj, painter, scene.sky_camera, viewport)

    def _draw_object(self, obj: SkyObject, painter: QPainter, camera: SkyCamera, viewport: QRect) -> None:
        if not self._is_visible(obj, camera):
            return
        
        point = camera.project(
                obj.get_position(), 
                viewport.size()
            )

        if point is None: 
            return
        
        match obj:
            case Star():
                self._draw_star(painter, obj, point)

            case Moon():
                self._draw_moon(painter, obj, point)

            case Satellite():
                self._draw_satellite(painter, obj, point)
            
            case Comet():
                self._draw_comet(painter, obj, point)
            
            case DeepSkyObject():
                self._draw_deep_sky_object(painter, obj, point)

            case _:
                raise TypeError(f"Unknown SkyObject type: {type(obj).__name__}")

    def _draw_star(self, painter: QPainter, star: Star, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        radius = self._get_star_radius(star.get_magnitude())
        painter.drawEllipse(point, radius, radius)

    def _draw_moon(self, painter: QPainter, moon: Moon, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 5, 5)
    
    def _draw_satellite(self, painter: QPainter, satellite: Satellite, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 3, 3)

    def _draw_comet(self, painter: QPainter, comet: Comet, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 4, 4)

    def _draw_deep_sky_object(self, painter: QPainter, deep_sky_object: DeepSkyObject, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 6, 6)

    
    def _get_star_radius(self, magnitude: Magnitude) -> float:
        radius = max(1.0, 3.0 - magnitude.value * 0.5)
        return radius
    

    def _is_visible(self, obj: SkyObject, camera: SkyCamera) -> bool:
        return obj.get_magnitude().is_visible(camera.limit_magnitude)
    
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



    def _draw_labels(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        for obj in scene.objects:
            if not self._is_visible(obj, scene.sky_camera):
                continue
            
            point = scene.sky_camera.project(
                obj.get_position(),
                viewport.size()
            )

            if point is None:
                continue
            
            if not self._should_draw_label(obj):
                continue

            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(point + LABEL_OFFSET, obj.name)


    def _should_draw_label(self, obj: SkyObject) -> bool:
        return True  # Placeholder for label visibility logic, can be based on magnitude or other criteria