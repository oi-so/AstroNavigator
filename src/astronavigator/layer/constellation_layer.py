from __future__ import annotations

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.constellation_renderer import ConstellationRenderer
from astronavigator.rendering.render_context import RendererContext

class ConstellationLayer(Layer):
    def __init__(self) -> None:
        super().__init__(visible=True, layer_type=LayerType.CONSTELLATION)

        self.renderer = ConstellationRenderer()

    # @profile
    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return

        if not context.scene.rendering_settings.show_constellation_lines:
            return

        self.renderer.render_lines(context)