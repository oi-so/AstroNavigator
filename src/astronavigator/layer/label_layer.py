from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPen

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.limiting_magnitude import calculate_limiting_magnitude
from astronavigator.rendering.render_context import RendererContext
from astronavigator.rendering.rendering_settings import RenderingSettings
from astronavigator.scene.scene import Scene
from astronavigator.sky.sky_object import SkyObject
from astronavigator.sky.object_type import ObjectType


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
        viewport = context.viewport
        projection = context.projection
        projection_context = context.projection_context

        limiting_magnitude = calculate_limiting_magnitude(
            scene.rendering_settings.limiting_magnitude,
            scene.sky_camera.fov_deg
        )

        min_position, max_position = context.projection.visible_bounds(context.projection_context, viewport.size())
        self._set_pen(painter, scene.rendering_settings.color_settings.constellation_label_color)

        for object_type in ObjectType:
            visible_objects = scene.object_index.find_visible_by_type(object_type, limiting_magnitude, min_position, max_position)

            for obj in visible_objects:
                if not self._should_draw_label(obj, scene.rendering_settings):
                    continue

                point = projection.project_object(obj, projection_context, viewport.size())

                if point is None:
                    continue

                painter.drawText(point + LABEL_OFFSET, obj.name)

    # @profile
    def _should_draw_label(self, obj: SkyObject, settings: RenderingSettings) -> bool:
        if not settings.show_labels:
            return False

        if obj.get_magnitude().value > settings.label_limiting_magnitude:
            return False

        if obj.name.startswith("HYG") and not settings.show_catalog_names:
            return False

        return True

    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)