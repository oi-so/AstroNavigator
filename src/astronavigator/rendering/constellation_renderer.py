from __future__ import annotations

from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import QPointF, QRectF, Qt

from astronavigator.rendering.render_context import RendererContext
from astronavigator.rendering.label_layout import BELOW_HORIZON_LABEL_ALPHA

class ConstellationRenderer:
    # @profile
    def render_lines(self, context: RendererContext) -> None:
        self._draw_constellation_lines(context)

    def render_labels(self, context: RendererContext) -> None:
        self._draw_constellation_labels(context)

    # @profile
    def _draw_constellation_lines(self, context: RendererContext) -> None:
        painter = context.painter
        scene = context.scene
        viewport_size = context.viewport.size()
        projection = context.projection

        painter.save()

        try:
            painter.setClipPath(
                projection.create_clip_path(
                    context.projection_context, viewport_size
                ),
                Qt.ClipOperation.IntersectClip
            )

            self._set_pen(painter, scene.rendering_settings.color_settings.constellation_line_color)

            # 線を共有する恒星は、同一フレーム内で一度だけ投影する。
            projected_endpoints = {}

            def project_endpoint(hip):
                if hip not in projected_endpoints:
                    star = scene.object_index.find_by_hip(int(hip))
                    if star is None:
                        projected_endpoints[hip] = (None, None)
                    else:
                        position = projection.convert_position(
                            star.get_position(scene.time, scene.observer), context.projection_context
                        )
                        visible = projection.project(position, context.projection_context, viewport_size)
                        projected_endpoints[hip] = (visible, position)
                return projected_endpoints[hip]

            for constellation in scene.constellations:
                for line in constellation.lines:
                    start_visible, start_position = project_endpoint(line.start_id)
                    end_visible, end_position = project_endpoint(line.end_id)
                    if start_visible is None and end_visible is None:
                        continue

                    if start_position is None or end_position is None:
                        continue
                    start_point = start_visible if start_visible is not None else projection.project_unclipped(
                        start_position, context.projection_context, viewport_size
                    )
                    end_point = end_visible if end_visible is not None else projection.project_unclipped(
                        end_position, context.projection_context, viewport_size
                    )
                    if start_point is None or end_point is None:
                        continue

                    painter.drawLine(start_point, end_point)
        finally:
            painter.restore()

    # @profile
    def _draw_constellation_labels(self, context: RendererContext) -> None:
        painter = context.painter
        scene = context.scene
        viewport = context.viewport
        projection = context.projection

        base_color = scene.rendering_settings.color_settings.constellation_label_color
        below_horizon_path = projection.create_below_horizon_path(context.projection_context, viewport.size())

        metrics = painter.fontMetrics()
        ascent = float(metrics.ascent())
        descent = float(metrics.descent())
        text_height = ascent + descent

        for constellation in scene.constellations:
            name = constellation.name
            converted = projection.convert_position(constellation.label_position, context.projection_context)
            point = projection.project(converted, context.projection_context, viewport.size())

            if point is None:
                continue

            text_width = float(metrics.horizontalAdvance(name))
            position = QPointF(point.x() - text_width / 2.0, point.y() + (ascent - descent) / 2.0)
            label_rect = QRectF(position.x(), position.y() - ascent, text_width, text_height)

            if not QRectF(viewport).intersects(label_rect):
                continue

            if not context.label_layout.try_reserve(label_rect):
                continue

            color = QColor(base_color)
            if below_horizon_path.contains(point):
                color.setAlpha(min(color.alpha(), BELOW_HORIZON_LABEL_ALPHA))

            self._set_pen(painter, color)
            painter.drawText(position, name)


    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)