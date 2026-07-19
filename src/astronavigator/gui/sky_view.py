from __future__ import annotations

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QKeyEvent, QPainter, Qt

from astronavigator.input.input_controller import InputController
from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene
from astronavigator.input.key_bindings import KEY_BINDINGS


class SkyView(QWidget):
    def __init__(self, scene: Scene, renderer: Renderer, input_controller: InputController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = scene
        self._renderer = renderer
        self._input_controller = input_controller
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        self._renderer.render(painter, self._scene, self.rect())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        action = KEY_BINDINGS.get(event.key())

        if action is None:
            super().keyPressEvent(event)
            return
        
        self._input_controller.handle_action(action)
        self.update()