from PySide6.QtCore import Qt

from .input_action import InputAction

Key = Qt.Key

KEY_BINDINGS: dict[int, InputAction] = {
    Key.Key_W: InputAction.MOVE_UP,
    Key.Key_S: InputAction.MOVE_DOWN,
    Key.Key_A: InputAction.MOVE_LEFT,
    Key.Key_D: InputAction.MOVE_RIGHT,

    Key.Key_Up: InputAction.MOVE_UP,
    Key.Key_Down: InputAction.MOVE_DOWN,
    Key.Key_Left: InputAction.MOVE_LEFT,
    Key.Key_Right: InputAction.MOVE_RIGHT,

    Key.Key_Q: InputAction.ZOOM_IN,
    Key.Key_E: InputAction.ZOOM_OUT,
}