from __future__ import annotations

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainter, QWheelEvent, Qt, QNativeGestureEvent
from PySide6.QtCore import QEvent, QPoint

from astronavigator.event.event_bus import EventBus
from astronavigator.input.input_controller import InputController
from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene
from astronavigator.input.key_bindings import KEY_BINDINGS
from astronavigator.event.event_type import EventType


DRAG_THRESHOLD_PX = 2

class SkyView(QWidget):
    def __init__(self, scene: Scene, renderer: Renderer, input_controller: InputController, event_bus: EventBus, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = scene
        self._renderer = renderer
        self._input_controller = input_controller
        self._event_bus = event_bus
        self._drag_start_position: QPoint | None = None
        self._dragging = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._event_bus.subscribe(EventType.TIME_CHANGED, self._on_time_changed)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        try:
            self._renderer.render(painter, self._scene, self.rect())
        finally:
            painter.end()

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
            self._drag_start_position = event.pos()
            self._dragging = False

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start_position is None:
            return

        current_position = event.pos()
        delta = current_position - self._drag_start_position

        if not self._dragging:
            if delta.manhattanLength() <= DRAG_THRESHOLD_PX:
                return

            self._dragging = True
            self._input_controller.begin_drag()

        self._input_controller.handle_drag(self._drag_start_position, current_position, self.rect().size())
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self._input_controller.end_drag()
            else:
                self._input_controller.handle_click(event.position(), self.rect().size())
                self._drag_start_position = None
                self._dragging = False

        self.update()
        super().mouseReleaseEvent(event)


    def _on_time_changed(self, event) -> None:
        self.update()