from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPen

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.render_context import RendererContext



class MountLayer(Layer):
    def __init__(self, visible: bool = True) -> None:
        super().__init__(visible=visible, layer_type=LayerType.MOUNT)

    def render(self, context: RendererContext) -> None:
        position = context.scene.mount_position

        if position is None:
            return

        projection_position = context.projection.convert_position(
            position, context.projection_context
        )

        point = context.projection.project(
            projection_position, context.projection_context, context.viewport.size()
        )

        if point is None:
            return

        settings = context.scene.rendering_settings
        radius = settings.mount_marker_radius
        outer = radius + 7
        gap = radius + 2

        painter = context.painter
        painter.save()

        pen = QPen(settings.color_settings.mount_marker_color)
        pen.setWidth(2)

        painter.setPen(pen)
        painter.setBrush(Qt.GlobalColor.transparent)

        painter.drawEllipse(point, radius, radius)

        painter.drawLine(QPointF(point.x() - outer, point.y()), QPointF(point.x() - gap, point.y()))
        painter.drawLine(QPointF(point.x() + outer, point.y()), QPointF(point.x() + gap, point.y()))
        painter.drawLine(QPointF(point.x(), point.y() - outer), QPointF(point.x(), point.y() - gap))
        painter.drawLine(QPointF(point.x(), point.y() + outer), QPointF(point.x(), point.y() + gap))

        painter.drawText(QPointF(point.x() + outer + 5, point.y() + 5), "Mount")

        painter.restore()