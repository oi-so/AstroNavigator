from __future__ import annotations

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainter, QWheelEvent, Qt, QNativeGestureEvent
from PySide6.QtCore import QEvent, QPoint

from astronavigator.input.input_controller import InputController
from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene
from astronavigator.input.key_bindings import KEY_BINDINGS


DRAG_THRESHOLD_PX = 2

class SkyView(QWidget):
    def __init__(self, scene: Scene, renderer: Renderer, input_controller: InputController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = scene
        self._renderer = renderer
        self._input_controller = input_controller
        self._last_mouse_position: QPoint | None = None
        self._dragging = False
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


    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        self._input_controller.handle_wheel(delta)
        self.update()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.NativeGesture:
            assert isinstance(event, QNativeGestureEvent)

            if event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                self._input_controller.handle_pinch(event.value())
                self.update()

            return True
        return super().event(event)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_position = event.pos()
            self._dragging = False

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._last_mouse_position is None:
            return

        delta = event.pos() - self._last_mouse_position
        if delta.manhattanLength() > DRAG_THRESHOLD_PX:
            self._dragging = True

        self._last_mouse_position = event.pos()

        self._input_controller.handle_drag(
            delta.x(),
            delta.y(),
            self.rect().size(),
        )

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._dragging:
                self._input_controller.handle_click(event.position(), self.rect().size())

            self._last_mouse_position = None
            self._dragging = False

        self.update()
        super().mouseReleaseEvent(event)