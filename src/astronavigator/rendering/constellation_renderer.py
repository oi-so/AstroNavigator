from __future__ import annotations

from PySide6.QtGui import QColor, QPainter, QPen

from astronavigator.rendering.render_context import RendererContext

class ConstellationRenderer:
    # profile
    def render(self, context: RendererContext) -> None:
        self._draw_constellation_lines(context)
        self._draw_constellation_labels(context)

    # profile
    def _draw_constellation_lines(self, context: RendererContext) -> None:
        painter = context.painter
        scene = context.scene
        viewport = context.viewport
        projection = context.projection

        self._set_pen(painter, scene.rendering_settings.color_settings.constellation_line_color)

        constellations = scene.constellations
        for constellation in constellations:
            for line in constellation.lines:

                start_pos = scene.object_index.find_by_hip(int(line.start_id))
                end_pos = scene.object_index.find_by_hip(int(line.end_id))

                if start_pos is None or end_pos is None:
                    continue

                start_pos_converted = projection.convert_position(
                    start_pos.get_position(),
                    context.projection_context
                )

                end_pos_converted = projection.convert_position(
                    end_pos.get_position(),
                    context.projection_context
                )


                p1 = projection.project(
                    start_pos_converted,
                    context.projection_context,
                    viewport.size()
                )

                p2 = projection.project(
                    end_pos_converted,
                    context.projection_context,
                    viewport.size()
                )

                if p1 and p2:
                    painter.drawLine(p1, p2)

    # profile
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