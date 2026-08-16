from __future__ import annotations

from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import Qt

from astronavigator.rendering.render_context import RendererContext

class ConstellationRenderer:
    # @profile
    def render(self, context: RendererContext) -> None:
        self._draw_constellation_lines(context)
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

            for constellation in scene.constellations:
                for line in constellation.lines:
                    start_object = scene.object_index.find_by_hip(int(line.start_id))
                    end_object = scene.object_index.find_by_hip(int(line.end_id))

                    if start_object is None or end_object is None:
                        continue

                    start_position = start_object.get_position(scene.time, scene.observer)
                    end_position = end_object.get_position(scene.time, scene.observer)

                    start_pos_converted = projection.convert_position(
                        start_position, context.projection_context
                    )

                    end_pos_converted = projection.convert_position(
                        end_position, context.projection_context
                    )

                    start_visible = projection.project(
                        start_pos_converted, context.projection_context, viewport_size
                    )

                    end_visible = projection.project(
                        end_pos_converted, context.projection_context, viewport_size
                    )

                    if start_visible is None and end_visible is None:
                        continue

                    start_point = start_visible
                    if start_visible is None:
                        start_point = projection.project_unclipped(
                            start_pos_converted, context.projection_context, viewport_size
                        )

                    end_point = end_visible
                    if end_visible is None:
                        end_point = projection.project_unclipped(
                            end_pos_converted, context.projection_context, viewport_size
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

        self._set_pen(painter, scene.rendering_settings.color_settings.constellation_label_color)
        constellations = scene.constellations
        for constellation in constellations:
            name = constellation.name
            label_position = constellation.label_position

            label_position_converted = projection.convert_position(label_position, context.projection_context)
            p = projection.project(label_position_converted, context.projection_context, viewport.size())
            if p:
                painter.drawText(p, name)


    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)