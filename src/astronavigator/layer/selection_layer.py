from __future__ import annotations

from PySide6.QtGui import Qt

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.render_context import RendererContext

SELECTION_RADIUS = 15


class SelectionLayer(Layer):
    def __init__(self) -> None:
        super().__init__(visible=True, layer_type=LayerType.SELECTION)

    def render(self, context: RendererContext) -> None:
        selected_obj = context.scene.selection.selected
        if selected_obj is None:
            return
        
        point = context.projection.project_object(
            selected_obj,
            context.projection_context,
            context.viewport.size()
        )

        if point is None:
            return

        color = context.scene.rendering_settings.color_settings.selection_color
        radius = context.scene.rendering_settings.selection_radius
        context.painter.setPen(color)
        context.painter.setBrush(Qt.GlobalColor.transparent)
        context.painter.drawEllipse(point, radius, radius)