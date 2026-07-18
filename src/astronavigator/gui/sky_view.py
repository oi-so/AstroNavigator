from __future__ import annotations

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter

from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene


class SkyView(QWidget):
    def __init__(self, scene: Scene, renderer: Renderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = scene
        self._renderer = renderer

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        self._renderer.render(painter, self._scene, self.rect())