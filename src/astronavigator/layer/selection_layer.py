from __future__ import annotations

from PySide6.QtGui import Qt

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.render_context import RendererContext
from astronavigator.sky.sky_object import Comet, Satellite

SELECTION_RADIUS = 15


class SelectionLayer(Layer):
    def __init__(self) -> None:
        super().__init__(visible=True, layer_type=LayerType.SELECTION)

    def render(self, context: RendererContext) -> None:
        selected_obj = context.scene.selection.selected
        if selected_obj is None:
            return

        if isinstance(selected_obj, Satellite):
            snapshot = context.scene.satellite_render_snapshot
            if snapshot is None:
                return
            state = snapshot.states.get(selected_obj.id)
            if state is None:
                return
            point = context.projection.project(
                state.observation.position,
                context.projection_context,
                context.viewport.size(),
            )
        elif isinstance(selected_obj, Comet):
            snapshot = context.scene.comet_render_snapshot
            if snapshot is None:
                return
            state = snapshot.states.get(selected_obj.id)
            if state is None:
                return
            point = context.projection.project(
                state.position,
                context.projection_context,
                context.viewport.size(),
            )
        else:
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