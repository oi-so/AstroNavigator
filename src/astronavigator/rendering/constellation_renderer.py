from __future__ import annotations

from PySide6.QtGui import QColor, QPainter, QPen

from astronavigator.rendering.render_context import RendererContext

class ConstellationRenderer:
    def render(self, context: RendererContext) -> None:
        self._draw_constellation_lines(context)
        self._draw_constellation_labels(context)


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

                p1 = projection.project(start_pos.get_position(), context.projection_context, viewport.size())
                p2 = projection.project(end_pos.get_position(), context.projection_context, viewport.size())

                if p1 and p2:
                    painter.drawLine(p1, p2)


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

            p = projection.project(label_position, context.projection_context, viewport.size())
            if p:
                painter.drawText(p, name)


    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)