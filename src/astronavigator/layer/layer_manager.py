from __future__ import annotations
from astronavigator.layer.layer import Layer, LayerType


class LayerManager:
    def __init__(self):
        self.layers: list[Layer] = []

    def add_layer(self, layer: Layer):
        self.layers.append(layer)
        self.layers.sort(key=lambda x: x.priority)

    def remove_layer(self, layer: Layer):
        self.layers.remove(layer)

    def get_visible_layers(self):
        return [layer for layer in self.layers if layer.visible]

    def find_layer(self, layer_type: LayerType) -> Layer | None:
        for layer in self.layers:
            if layer.layer_type == layer_type:
                return layer
        return None