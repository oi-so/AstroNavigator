from __future__ import annotations
from astronavigator.layer.layer import Layer, LayerType


class LayerManager:
    def __init__(self):
        self.layers: list[Layer] = []

    def add_layer(self, layer: Layer):
        self.layers.append(layer)

    def render(self, painter, scene, viewport):
        for layer in self.layers:
            layer.render(painter, scene, viewport)

    def get(self, layer_type: LayerType) -> Layer | None:
        for layer in self.layers:
            if layer.layer_type == layer_type:
                return layer
            
        return None