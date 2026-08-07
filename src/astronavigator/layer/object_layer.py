from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.limiting_magnitude import calculate_limiting_magnitude
from astronavigator.rendering.star_color import STAR_COLORS
from astronavigator.rendering.star_size import calculate_star_radius
from astronavigator.scene.scene import Scene
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import Comet, Moon, Satellite, SkyObject, Star, DeepSkyObject, Asteroid, Planet
from astronavigator.sky.magnitude import Magnitude
from astronavigator.rendering.render_context import RendererContext

class ObjectLayer(Layer):
    def __init__(self, visible: bool = True):
        super().__init__(visible=visible, layer_type=LayerType.OBJECTS)

        self.show_stars = True
        self.show_planets = True
        self.show_satellites = True
        self.show_deep_sky_objects = True
        self.show_comets = True
        self.show_asteroids = True
        self.show_moon = True
        self.limit_magnitude = 6.0

    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return

        limit_magnitude = calculate_limiting_magnitude(context.scene.rendering_settings.limiting_magnitude, context.scene.sky_camera.fov_deg)

        if self.show_stars:
            for obj in context.scene.object_index.find_by_type(ObjectType.STAR):
                self._draw_object(obj, context)

        if self.show_deep_sky_objects:
                for obj in context.scene.object_index.find_by_type(ObjectType.DSO):
                    self._draw_object(obj, context)

        if self.show_asteroids:
            for obj in context.scene.object_index.find_by_type(ObjectType.ASTEROID):
                self._draw_object(obj, context)

        if self.show_comets:
            for obj in context.scene.object_index.find_by_type(ObjectType.COMET):
                self._draw_object(obj, context)

        if self.show_planets:
            for obj in context.scene.object_index.find_by_type(ObjectType.PLANET):
                self._draw_object(obj, context)

        if self.show_moon:
            for obj in context.scene.object_index.find_by_type(ObjectType.MOON):
                self._draw_object(obj, context)

        if self.show_satellites:
            for obj in context.scene.object_index.find_by_type(ObjectType.SATELLITE):
                self._draw_object(obj, context)



    def _draw_object(self, obj: SkyObject, context: RendererContext) -> None:
        if not self._is_visible(context.scene, obj):
            return
        
        point = context.projection.project(
                obj.get_position(), 
                context.projection_context,
                context.viewport.size()
            )

        if point is None: 
            return

        
        match obj:
            case Star():
                self._draw_star(context.painter, obj, context.scene, point)

            case Moon():
                self._draw_moon(context.painter, obj, context.scene, point)

            case Satellite():
                self._draw_satellite(context.painter, obj, context.scene, point)
            
            case Comet():
                self._draw_comet(context.painter, obj, context.scene, point)
            
            case DeepSkyObject():
                self._draw_deep_sky_object(context.painter, obj, context.scene, point)

            case Planet():
                raise NotImplementedError("Planet rendering is not implemented yet.")

            case Asteroid():
                self._draw_star(context.painter, obj, context.scene, point)

            case _:
                raise TypeError(f"Unknown SkyObject type: {type(obj).__name__}")

    def _draw_star(self, painter: QPainter, star: Star | Asteroid, scene: Scene, point: QPointF) -> None:
        painter.setPen(STAR_COLORS[star.spectral_type])
        painter.setBrush(STAR_COLORS[star.spectral_type])
        radius = self._get_star_radius(star.get_magnitude(), scene.sky_camera.fov_deg)
        painter.drawEllipse(point, radius, radius)

    def _draw_moon(self, painter: QPainter, moon: Moon, scene: Scene, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 5, 5)
    
    def _draw_satellite(self, painter: QPainter, satellite: Satellite, scene: Scene, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 3, 3)

    def _draw_comet(self, painter: QPainter, comet: Comet, scene: Scene, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 4, 4)

    def _draw_deep_sky_object(self, painter: QPainter, deep_sky_object: DeepSkyObject, scene: Scene, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 6, 6)

    def _is_visible(self, scene: Scene, obj: SkyObject) -> bool:
        limit_magnitude = calculate_limiting_magnitude(scene.rendering_settings.limiting_magnitude, scene.sky_camera.fov_deg)
        return obj.get_magnitude().is_visible(limit_magnitude)


    
    def _get_star_radius(self, magnitude: Magnitude, camera_fov_deg: float) -> float:
        radius = calculate_star_radius(magnitude, camera_fov_deg)
        return radius


    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)