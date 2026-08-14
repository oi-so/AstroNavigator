from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPen

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.limiting_magnitude import calculate_limiting_magnitude
from astronavigator.rendering.star_color import STAR_COLORS
from astronavigator.rendering.star_size import calculate_star_radius
from astronavigator.scene.scene import Scene
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Comet, Moon, Satellite, SkyObject, Star, DeepSkyObject, Asteroid, Planet, Sun
from astronavigator.sky.magnitude import Magnitude
from astronavigator.rendering.render_context import RendererContext


PLANET_COLORS = {
    "solar_system:mercury": QColor(190, 190, 190),
    "solar_system:venus": QColor(255, 220, 150),
    "solar_system:mars": QColor(230, 110, 70),
    "solar_system:jupiter": QColor(225, 190, 150),
    "solar_system:saturn": QColor(235, 210, 150),
    "solar_system:uranus": QColor(150, 220, 230),
    "solar_system:neptune": QColor(100, 140, 240),
}


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
        self.show_sun = True

    # @profile
    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return

        limit_magnitude = calculate_limiting_magnitude(context.scene.rendering_settings.limiting_magnitude, context.scene.sky_camera.fov_deg)
        viewport_size = context.viewport.size()

        min_position, max_position = context.projection.visible_bounds(context.projection_context, viewport_size)

        if self.show_stars:
            self._render_type(ObjectType.STAR, limit_magnitude, viewport_size, context, min_position, max_position)

        if self.show_deep_sky_objects:
            self._render_type(ObjectType.DSO, limit_magnitude, viewport_size, context, min_position, max_position)

        if self.show_asteroids:
            self._render_type(ObjectType.ASTEROID, limit_magnitude, viewport_size, context, min_position, max_position)

        if self.show_comets:
            self._render_type(ObjectType.COMET, limit_magnitude, viewport_size, context, min_position, max_position)

        if self.show_planets:
            self._render_type(ObjectType.PLANET, limit_magnitude, viewport_size, context, min_position, max_position)

        if self.show_moon:
            self._render_type(ObjectType.MOON, limit_magnitude, viewport_size, context, min_position, max_position)

        if self.show_sun:
            self._render_type(ObjectType.SUN, limit_magnitude, viewport_size, context, min_position, max_position)

        if self.show_satellites:
            self._render_type(ObjectType.SATELLITE, limit_magnitude, viewport_size, context, min_position, max_position)


    # @profile
    def _render_type(self, object_type: ObjectType, limit_magnitude: float, viewport_size: QSize, context: RendererContext, min_position: Position, max_position: Position) -> None:
        fixed_objects = context.scene.object_index.find_visible_by_type(object_type, limit_magnitude, min_position, max_position)
        for obj in fixed_objects:
            self._render_object(obj, limit_magnitude, viewport_size, context)

        dynamic_objects = context.scene.object_index.find_dynamic_by_type(object_type)
        for obj in dynamic_objects:
            self._render_object(obj, limit_magnitude, viewport_size, context)

    def _render_object(self, obj: SkyObject, limit_magnitude: float, viewport_size: QSize, context: RendererContext) -> None:
        magnitude = obj.get_magnitude(context.scene.time, context.scene.observer)
        if not magnitude.is_visible(limit_magnitude):
            return

        point = context.projection.project_object(obj, context.projection_context, viewport_size)
        if point is None:
            return

        self._draw_object(obj, point, context, magnitude)


    def _draw_object(self, obj: SkyObject, point: QPointF, context: RendererContext, magnitude: Magnitude) -> None:
        match obj:
            case Star():
                self._draw_star(context.painter, obj, context.scene, point, magnitude)

            case Moon():
                self._draw_moon(context.painter, obj, context.scene, point)

            case Satellite():
                self._draw_satellite(context.painter, obj, context.scene, point)
            
            case Comet():
                self._draw_comet(context.painter, obj, context.scene, point)
            
            case DeepSkyObject():
                self._draw_deep_sky_object(context.painter, obj, context.scene, point)

            case Planet():
                self._draw_planet(context.painter, obj, point)

            case Asteroid():
                self._draw_star(context.painter, obj, context.scene, point, magnitude)

            case Sun():
                self._draw_sun(context.painter, point)

            case _:
                raise TypeError(f"Unknown SkyObject type: {type(obj).__name__}")

    def _draw_star(self, painter: QPainter, star: Star | Asteroid, scene: Scene, point: QPointF, magnitude: Magnitude) -> None:
        painter.setPen(STAR_COLORS[star.spectral_type])
        painter.setBrush(STAR_COLORS[star.spectral_type])
        radius = self._get_star_radius(magnitude, scene.sky_camera.fov_deg)
        painter.drawEllipse(point, radius, radius)

    def _draw_sun(self, painter: QPainter, point: QPointF) -> None:
        color = QColor(255, 220, 80)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawEllipse(point, 10, 10)

    def _draw_planet(self, painter: QPainter, planet: Planet, point: QPointF) -> None:
        color = PLANET_COLORS.get(planet.id, QColor(230, 230, 230))
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawEllipse(point, 4.0, 4.0)

    def _draw_moon(self, painter: QPainter, moon: Moon, scene: Scene, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 10, 10)
    
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
    
    def _get_star_radius(self, magnitude: Magnitude, camera_fov_deg: float) -> float:
        radius = calculate_star_radius(magnitude, camera_fov_deg)
        return radius


    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)