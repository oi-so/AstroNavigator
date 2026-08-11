from __future__ import annotations

from typing import TypeVar, Generic
from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, Qt

from astronavigator.layer.constellation_layer import ConstellationLayer
from astronavigator.layer.grid_layer import GridLayer
from astronavigator.layer.label_layer import LabelLayer
from astronavigator.layer.layer_manager import LayerManager
from astronavigator.layer.mount_layer import MountLayer
from astronavigator.layer.object_layer import ObjectLayer
from astronavigator.layer.selection_layer import SelectionLayer
from astronavigator.rendering.projection.projection_manager import ProjectionManager
from astronavigator.rendering.render_context import RendererContext
from astronavigator.scene.scene import Scene


P = TypeVar("P")
C = TypeVar("C")


class Renderer(Generic[P, C]):
    def __init__(self, projection_manager: ProjectionManager[P, C]) -> None:
        self._projection_manager = projection_manager
        self.layer_manager = LayerManager()

        self.layer_manager.add_layer(GridLayer())
        self.layer_manager.add_layer(ConstellationLayer())
        self.layer_manager.add_layer(ObjectLayer())
        self.layer_manager.add_layer(LabelLayer())
        self.layer_manager.add_layer(MountLayer())
        self.layer_manager.add_layer(SelectionLayer())


    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        projection_context = self._projection_manager.create_context(scene)
        context = RendererContext(
            painter=painter,
            scene=scene,
            viewport=viewport,
            projection=self._projection_manager.projection,
            projection_context=projection_context
        )

        self._draw_background(context)

        self.layer_manager.render(context)


    def _draw_background(self, context: RendererContext) -> None:
        painter = context.painter
        viewport = context.viewport

        painter.fillRect(viewport, Qt.GlobalColor.black)

        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)
