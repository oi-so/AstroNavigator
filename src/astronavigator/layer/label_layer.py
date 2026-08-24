from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.label_layout import BELOW_HORIZON_LABEL_ALPHA
from astronavigator.rendering.limiting_magnitude import calculate_label_limiting_magnitude
from astronavigator.rendering.render_context import RendererContext
from astronavigator.rendering.rendering_settings import RenderingSettings
from astronavigator.sky.sky_object import Satellite, SkyObject
from astronavigator.sky.object_type import ObjectType


LABEL_MARGIN = 5.0

OBJECT_LABEL_PRIORITY = {
    ObjectType.SUN: 0,
    ObjectType.MOON: 1,
    ObjectType.PLANET: 2,
    ObjectType.STAR: 3,
    ObjectType.DSO: 4,
    ObjectType.SATELLITE: 5,
    ObjectType.COMET: 6,
    ObjectType.ASTEROID: 7,
}


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
        scene = context.scene
        viewport_size = context.viewport.size()

        limiting_magnitude = calculate_label_limiting_magnitude(scene.rendering_settings.wide_label_limiting_magnitude, scene.rendering_settings.label_limiting_magnitude, scene.sky_camera.fov_deg)
        min_position, max_position = context.projection.visible_bounds(context.projection_context, viewport_size)

        candidates: list[tuple[int, float, str, SkyObject]] = []

        below_horizon_path = context.projection.create_below_horizon_path(context.projection_context, viewport_size)
        base_color = scene.rendering_settings.color_settings.constellation_label_color

        for object_type in ObjectType:
            fixed_objects = scene.object_index.find_visible_by_type(
                object_type, limiting_magnitude, min_position, max_position
            )
            dynamic_objects = scene.object_index.find_dynamic_by_type(object_type)

            snapshot = scene.satellite_render_snapshot
            for obj in (*fixed_objects, *dynamic_objects):
                if isinstance(obj, Satellite):
                    if snapshot is None:
                        continue

                    if obj.id not in snapshot.states:
                        continue
                    magnitude = snapshot.states[obj.id].brightness.magnitude
                else:
                    magnitude = obj.get_magnitude(scene.time, scene.observer)
                
                if not magnitude.is_visible(limiting_magnitude):
                    continue

                if not self._should_draw_label(obj, scene.rendering_settings):
                    continue

                candidates.append((
                    OBJECT_LABEL_PRIORITY.get(obj.object_type, 100),
                    magnitude.value, obj.name, obj
                ))

        candidates.sort(key=lambda x: (x[0], x[1], x[2]))
        for _, _, _, obj in candidates:
            self._draw_label(obj, context, below_horizon_path, base_color)

    def _draw_label(self, obj: SkyObject, context: RendererContext, below_horizon_path: QPainterPath, base_color: QColor) -> None:
        snapshot = context.scene.satellite_render_snapshot
        painter = context.painter

        if isinstance(obj, Satellite):
            if snapshot is None:
                return

            state = snapshot.states.get(obj.id)
            if state is None:
                return

            point = context.projection.project(state.observation.position, context.projection_context, context.viewport.size())
        else:
            point = context.projection.project_object(
                obj, context.projection_context, context.viewport.size()
            )
            
        if point is None:
            return

        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(obj.name)
        ascent = float(metrics.ascent())
        text_height = ascent + float(metrics.descent())

        candidate_positions = (
            QPointF(point.x() + LABEL_MARGIN, point.y() - LABEL_MARGIN),
            QPointF(point.x() + LABEL_MARGIN, point.y() + LABEL_MARGIN + ascent),
            QPointF(point.x() - LABEL_MARGIN - text_width, point.y() - LABEL_MARGIN),
            QPointF(point.x() - LABEL_MARGIN - text_width, point.y() + LABEL_MARGIN + ascent),
        )
        viewport_rect = QRectF(context.viewport)

        for position in candidate_positions:
            label_rect = QRectF(position.x(), position.y() - ascent, text_width, text_height)
            if not viewport_rect.contains(label_rect):
                continue
            if not context.label_layout.try_reserve(label_rect):
                continue

            color = QColor(base_color)
            if below_horizon_path.contains(point):
                color.setAlpha(min(color.alpha(), BELOW_HORIZON_LABEL_ALPHA))

            self._set_pen(painter, color)
            painter.drawText(position, obj.name)
            return


    # @profile
    def _should_draw_label(self, obj: SkyObject, settings: RenderingSettings) -> bool:
        if not settings.show_labels:
            return False

        return True

    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)