from __future__ import annotations
from dataclasses import dataclass
import math

from PySide6.QtCore import QPointF, QRectF, Qt, QSize
from PySide6.QtGui import QColor, QImage, QPainter, QPen

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
from astronavigator.sky.dso_type import DeepSkyObjectType


SELECTION_THRESHOLD = 20.0 # px

MOON_RADIUS_PX = 10.0
MOON_PHASE_IMAGE_SIZE = 64
MOON_OUTLINE_SIZE = 0.1

MOON_LIGHT_COLOR = QColor(245, 245, 220)
MOON_DARK_COLOR = QColor(45, 48, 55)


PLANET_COLORS = {
    "solar_system:mercury": QColor(190, 190, 190),
    "solar_system:venus": QColor(255, 220, 150),
    "solar_system:mars": QColor(230, 110, 70),
    "solar_system:jupiter": QColor(225, 190, 150),
    "solar_system:saturn": QColor(235, 210, 150),
    "solar_system:uranus": QColor(150, 220, 230),
    "solar_system:neptune": QColor(100, 140, 240),
}


@dataclass(slots=True)
class RenderedObject:
    obj: SkyObject
    point: QPointF
    


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

        self._render_objects: list[RenderedObject] = []

        self._moon_phase_image_fraction: float | None = None
        self._moon_phase_image: QImage | None = None

    # @profile
    def render(self, context: RendererContext) -> None:
        self._render_objects.clear()
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

        if self.show_sun:
            self._render_type(ObjectType.SUN, limit_magnitude, viewport_size, context, min_position, max_position)

        if self.show_moon:
            self._render_type(ObjectType.MOON, limit_magnitude, viewport_size, context, min_position, max_position)

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
        scene = context.scene
        time = scene.time
        observer = scene.observer

        if isinstance(obj, Comet):
            snapshot = scene.comet_render_snapshot
            if snapshot is None:
                return

            state = snapshot.states.get(obj.id)
            if state is None:
                return

            point = context.projection.project(state.position, context.projection_context, viewport_size)
            if point is None:
                return

            magnitude = state.magnitude
            comet_limit = getattr(scene.rendering_settings, "comet_limiting_magnitude", limit_magnitude)
            if not magnitude.is_visible(comet_limit):
                return

        elif isinstance(obj, Satellite):
            snapshot = scene.satellite_render_snapshot
            if snapshot is None:
                return

            state = snapshot.states.get(obj.id)
            if state is None:
                return

            observation = state.observation
            if observation.altitude_deg < 0.0:
                return

            point = context.projection.project(observation.position, context.projection_context, viewport_size)
            if point is None:
                return

            magnitude = state.brightness.magnitude
            satellite_limit = getattr(scene.rendering_settings, "satellite_limiting_magnitude", limit_magnitude)

            if not magnitude.is_visible(satellite_limit):
                return

        else:
            point = context.projection.project_object(obj, context.projection_context, viewport_size)

            if point is None:
                return

            magnitude = obj.get_magnitude(time, observer)

            if not magnitude.is_visible(limit_magnitude):
                return

        self._draw_object(obj, point, context, magnitude)
        self._render_objects.append(RenderedObject(obj, point))


    def _draw_object(self, obj: SkyObject, point: QPointF, context: RendererContext, magnitude: Magnitude) -> None:
        match obj:
            case Star():
                self._draw_star(context.painter, obj, context.scene, point, magnitude)

            case Moon():
                self._draw_moon(context, obj, point)

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

    def _draw_moon(self, context: RendererContext, moon: Moon, point: QPointF) -> None:
        scene = context.scene
        viewport_size = context.viewport.size()
        time, observer = scene.time, scene.observer

        phase_info = moon.get_phase_info(time, observer)
        bright_limb_position = moon.get_bright_limb_position(time=time, observer=observer)

        converted_position = context.projection.convert_position(bright_limb_position, context.projection_context)
        bright_limb_point = context.projection.project_unclipped(converted_position, context.projection_context, viewport_size)

        if bright_limb_point is None:
            bright_direction_x = 1.0
            bright_direction_y = 0.0
        else:
            bright_direction_x = bright_limb_point.x() - point.x()
            bright_direction_y = bright_limb_point.y() - point.y()
            length = math.hypot(bright_direction_x, bright_direction_y)

            if length < 1e-8:
                bright_direction_x = 1.0
                bright_direction_y = 0.0
            else:
                bright_direction_x /= -length
                bright_direction_y /= -length

        image = self._get_moon_phase_image(phase_info.illuminated_fraction)

        direction_angle_deg = math.degrees(math.atan2(bright_direction_y, bright_direction_x))
        rotate_rect = QRectF(-MOON_RADIUS_PX, -MOON_RADIUS_PX, MOON_RADIUS_PX * 2.0, MOON_RADIUS_PX * 2.0)

        painter = context.painter
        painter.save()

        try:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.translate(point)
            painter.rotate(direction_angle_deg)
            painter.drawImage(rotate_rect, image)

            outline_pen = QPen(QColor(200, 200, 200))
            outline_pen.setWidthF(MOON_OUTLINE_SIZE)
            painter.setPen(outline_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(0.0, 0.0), MOON_RADIUS_PX, MOON_RADIUS_PX)
        finally:
            painter.restore()

    
    def _draw_satellite(self, painter: QPainter, satellite: Satellite, scene: Scene, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 1, 1)

    def _draw_comet(self, painter: QPainter, comet: Comet, scene: Scene, point: QPointF) -> None:
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(point, 4, 4)

    def _draw_deep_sky_object(self, painter: QPainter, deep_sky_object: DeepSkyObject, scene: Scene, point: QPointF) -> None:
        color = QColor(100, 180, 255)

        pen = QPen(color)
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        dso_type = deep_sky_object.dso_type
        galaxy_types = {
            DeepSkyObjectType.GALAXY,
            DeepSkyObjectType.GALAXY_PAIR,
            DeepSkyObjectType.GALAXY_TRIPLET,
            DeepSkyObjectType.GALAXY_GROUP,
        }

        nebula_types = {
            DeepSkyObjectType.PLANETARY_NEBULA,
            DeepSkyObjectType.HII_REGION,
            DeepSkyObjectType.DARK_NEBULA,
            DeepSkyObjectType.EMISSION_NEBULA,
            DeepSkyObjectType.REFLECTION_NEBULA,
            DeepSkyObjectType.NEBULA,
            DeepSkyObjectType.SUPERNOVA_REMNANT,
            DeepSkyObjectType.CLUSTER_AND_NEBULA,
        }

        if dso_type in galaxy_types:
            painter.drawEllipse(point, 6.0, 3.5)

        elif dso_type == DeepSkyObjectType.OPEN_CLUSTER:
            pen.setStyle(Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawEllipse(point, 5.0, 5.0)
            
        elif dso_type == DeepSkyObjectType.GLOBULAR_CLUSTER:
            painter.drawEllipse(point, 5.0, 5.0)
            painter.drawLine(
                QPointF(point.x() - 5.0, point.y()),
                QPointF(point.x() + 5.0, point.y()),
            )
            painter.drawLine(
                QPointF(point.x(), point.y() - 5.0),
                QPointF(point.x(), point.y() + 5.0),
            )

        elif dso_type in nebula_types:
            painter.drawRect(
                QRectF(
                    point.x() - 4.0,
                    point.y() - 4.0,
                    8.0,
                    8.0,
                )
            )

        else:
            painter.drawEllipse(point, 3.0, 3.0)

    
    def _get_star_radius(self, magnitude: Magnitude, camera_fov_deg: float) -> float:
        radius = calculate_star_radius(magnitude, camera_fov_deg)
        return radius


    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)



    def find_nearest_object(self, point: QPointF) -> SkyObject | None:
        best_object: SkyObject | None = None
        best_distance2 = SELECTION_THRESHOLD ** 2

        for rendered in reversed(self._render_objects):
            dx = rendered.point.x() - point.x()
            dy = rendered.point.y() - point.y()
            distance2 = dx * dx + dy * dy
            if distance2 < best_distance2:
                best_distance2 = distance2
                best_object = rendered.obj

        return best_object



    @staticmethod
    def _create_moon_phase_image(illuminated_fraction: float, bright_direction_x: float, bright_direction_y: float) -> QImage:
        radius = MOON_PHASE_IMAGE_SIZE / 2
        center = (MOON_PHASE_IMAGE_SIZE - 1) / 2.0

        image = QImage(MOON_PHASE_IMAGE_SIZE, MOON_PHASE_IMAGE_SIZE, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)

        illuminated_fraction = max(0.0, min(1.0, illuminated_fraction))

        illumination_angle = math.acos(2.0 * illuminated_fraction - 1.0)

        sin_angle = math.sin(illumination_angle)
        cos_angle = math.cos(illumination_angle)

        for y in range(MOON_PHASE_IMAGE_SIZE):
            for x in range(MOON_PHASE_IMAGE_SIZE):
                screen_x = (x - center) / radius
                screen_y = (y - center) / radius

                distance2 = screen_x * screen_x + screen_y * screen_y

                if distance2 > 1.0:
                    continue

                local_x = screen_x * bright_direction_x + screen_y * bright_direction_y
                local_y = -screen_x * bright_direction_y + screen_y * bright_direction_x

                surface_z = math.sqrt(max(0.0, 1.0 - local_x * local_x - local_y * local_y))
                light_dot_normal = local_x * sin_angle + surface_z * cos_angle

                if light_dot_normal > 0.0:
                    color = MOON_LIGHT_COLOR
                else:
                    color = MOON_DARK_COLOR

                image.setPixelColor(x, y, color)

        return image


    def _get_moon_phase_image(self, illuminated_fraction: float) -> QImage:
        if self._moon_phase_image is None or self._moon_phase_image_fraction != illuminated_fraction:
            self._moon_phase_image = self._create_moon_phase_image(illuminated_fraction, 1.0, 0.0)
            self._moon_phase_image_fraction = illuminated_fraction

        return self._moon_phase_image