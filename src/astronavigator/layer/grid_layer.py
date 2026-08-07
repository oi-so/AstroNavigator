from __future__ import annotations


from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.grid_renderer import EquatorialGridRenderer
from astronavigator.rendering.render_context import RendererContext

class GridLayer(Layer):
    def __init__(self) -> None:
        super().__init__(visible=True, layer_type=LayerType.GRID)

        self.renderer = EquatorialGridRenderer()

    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return

        self.renderer.render(context)