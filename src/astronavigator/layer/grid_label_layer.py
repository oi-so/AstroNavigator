from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QFont

from astronavigator.layer.grid_layer import GridLabel, GridLabelEdge, GridLayer
from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.render_context import RendererContext


GRID_LABEL_MARGIN = 4.0
NSEW_LABEL_SIZE = 30.0


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
            base_font = QFont(painter.font())

            labels = sorted(self._grid_layer.labels, key=lambda label: label.offset_direction is None)

            for label in labels:
                font = QFont(base_font)
                if label.offset_direction is not None:
                    font.setPointSizeF(NSEW_LABEL_SIZE)

                painter.setFont(font)
                position = self._calculate_label_position(context, label)

                metrics = painter.fontMetrics()
                text_width = float(metrics.horizontalAdvance(label.text))

                text_rect = QRectF(
                    position.x(),
                    position.y() - float(metrics.ascent()),
                    text_width,
                    float(metrics.height()),
                )

                if not context.label_layout.try_reserve(text_rect):
                    continue

                painter.setPen(label.color)
                painter.drawText(position, label.text)

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

        if label.offset_direction is not None:
            text_height = ascent + descent
            label_center_x = label.anchor.x() + label.offset_direction.x() * (text_width / 2.0 + GRID_LABEL_MARGIN)
            label_center_y = label.anchor.y() + label.offset_direction.y() * (text_height / 2.0 + GRID_LABEL_MARGIN)

            text_x = label_center_x - text_width / 2.0
            baseline_y = label_center_y + (ascent - descent) / 2.0

        elif label.edge == GridLabelEdge.TOP:
            text_x = label.anchor.x() - text_width / 2.0
            baseline_y = label.anchor.y() + ascent + GRID_LABEL_MARGIN
        elif label.edge == GridLabelEdge.BOTTOM:
            text_x = label.anchor.x() - text_width / 2.0
            baseline_y = label.anchor.y() - descent - GRID_LABEL_MARGIN
        elif label.edge == GridLabelEdge.LEFT:
            text_x = label.anchor.x() + GRID_LABEL_MARGIN
            baseline_y = label.anchor.y() + (ascent - descent) / 2.0
        elif label.edge == GridLabelEdge.RIGHT:
            text_x = label.anchor.x() - text_width - GRID_LABEL_MARGIN
            baseline_y = label.anchor.y() + (ascent - descent) / 2.0
        else:
            raise ValueError(f"Invalid edge value: {label.edge}")

        text_x = max(GRID_LABEL_MARGIN, min(text_x, width - text_width - GRID_LABEL_MARGIN))
        baseline_y = max(ascent + GRID_LABEL_MARGIN, min(baseline_y, height - descent - GRID_LABEL_MARGIN))

        return QPointF(text_x, baseline_y)