from __future__ import annotations

from PySide6.QtCore import QPointF

from astronavigator.layer.grid_layer import GridLabel, GridLayer
from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.render_context import RendererContext


GRID_LABEL_MARGIN = 4.0


class GridLabelLayer(Layer):
    def __init__(self, grid_layer: GridLayer) -> None:
        super().__init__(visible=True, layer_type=LayerType.GRID)
        self._grid_layer = grid_layer

    def render(self, context: RendererContext) -> None:
        if not self.visible or not self._grid_layer.visible:
            return

        painter = context.painter
        painter.save()

        try:
            for label in self._grid_layer.labels:
                painter.setPen(label.color)
                painter.drawText(self._calculate_label_position(context, label), label.text)
        finally:
            painter.restore()

    @staticmethod
    def _calculate_label_position(context: RendererContext, label: GridLabel) -> QPointF:
        painter = context.painter
        metrics = painter.fontMetrics()

        width = float(context.viewport.width())
        height = float(context.viewport.height())

        text_width = float(metrics.horizontalAdvance(label.text))
        ascent = float(metrics.ascent())
        descent = float(metrics.descent())

        point = label.anchor

        edge_distances = (point.x(), width - point.x(), point.y(), height - point.y())
        closest_edge = min(range(len(edge_distances)), key=lambda i: edge_distances[i])

        min_baseline = GRID_LABEL_MARGIN + ascent
        max_baseline = height - GRID_LABEL_MARGIN - descent

        centered_baseline = point.y() + (ascent - descent) / 2
        baseline_y = max(min_baseline, min(max_baseline, centered_baseline))

        if closest_edge == 0:
            return QPointF(GRID_LABEL_MARGIN, baseline_y)
        elif closest_edge == 1:
            return QPointF(width - GRID_LABEL_MARGIN - text_width, baseline_y)

        centered_x = point.x() - text_width / 2
        text_x = max(GRID_LABEL_MARGIN, min(width - GRID_LABEL_MARGIN - text_width, centered_x))

        if closest_edge == 2:
            return QPointF(text_x, GRID_LABEL_MARGIN + ascent)
        else:
            return QPointF(text_x, height - GRID_LABEL_MARGIN - descent)