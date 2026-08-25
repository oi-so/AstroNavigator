from __future__ import annotations
from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.render_context import RendererContext


class LayerManager:
    def __init__(self):
        self._layers: list[Layer] = []

    def add_layer(self, layer: Layer):
        self._layers.append(layer)

    def render(self, context: RendererContext):
        for layer in self._layers:

            if layer.visible:
                layer.render(context)


    def set_visible(self, layer_type: LayerType, visible: bool) -> None:
        for layer in self._layers:
            if layer.layer_type == layer_type:
                layer.visible = visible

    def get_visible(self, layer_type: LayerType) -> bool | None:
        matching_layers = [layer for layer in self._layers if layer.layer_type == layer_type]
        if not matching_layers:
            return None
        return all(layer.visible for layer in matching_layers)

    def get(self, layer_type: LayerType) -> Layer | None:
        for layer in self._layers:
            if layer.layer_type == layer_type:
                return layer
            
        return None