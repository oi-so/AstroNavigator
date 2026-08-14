from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPen

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.limiting_magnitude import calculate_limiting_magnitude
from astronavigator.rendering.render_context import RendererContext
from astronavigator.rendering.rendering_settings import RenderingSettings
from astronavigator.sky.sky_object import SkyObject
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.magnitude import Magnitude


LABEL_OFFSET = QPointF(5, -5)


class LabelLayer(Layer):
    def __init__(self, visible: bool = True):
        super().__init__(visible=visible, layer_type=LayerType.LABELS)


    # @profile
    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return

        self._draw_labels(context)

    # @profile
    def _draw_labels(self, context: RendererContext) -> None:
        painter = context.painter
        scene = context.scene
        viewport_size = context.viewport.size()

        limiting_magnitude = calculate_limiting_magnitude(scene.rendering_settings.label_limiting_magnitude, scene.sky_camera.fov_deg)
        min_position, max_position = context.projection.visible_bounds(context.projection_context, viewport_size)
        self._set_pen(painter, scene.rendering_settings.color_settings.constellation_label_color)

        for object_type in ObjectType:
            fixed_objects = scene.object_index.find_visible_by_type(
                object_type, limiting_magnitude, min_position, max_position
            )
            for obj in fixed_objects:
                self._draw_label(obj, limiting_magnitude, context)

            dynamic_objects = scene.object_index.find_dynamic_by_type(object_type)
            for obj in dynamic_objects:
                self._draw_label(obj, limiting_magnitude, context)

    def _draw_label(self, obj: SkyObject, limiting_magnitude: float, context: RendererContext) -> None:
        scene = context.scene
        magnitude = obj.get_magnitude(scene.time, scene.observer)

        if not magnitude.is_visible(limiting_magnitude):
            return

        if not self._should_draw_label(obj, magnitude, scene.rendering_settings):
            return

        point = context.projection.project_object(
            obj, context.projection_context, context.viewport.size()
        )
        if point is None:
            return

        context.painter.drawText(point + LABEL_OFFSET, obj.name)


    # @profile
    def _should_draw_label(self, obj: SkyObject, magnitude: Magnitude, settings: RenderingSettings) -> bool:
        if not settings.show_labels:
            return False

        if magnitude.value > settings.label_limiting_magnitude:
            return False

        if obj.name.startswith("HYG") and not settings.show_catalog_names:
            return False

        return True

    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)