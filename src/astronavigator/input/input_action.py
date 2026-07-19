from enum import Enum, auto


class InputAction(Enum):
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()

    ZOOM_IN = auto()
    ZOOM_OUT = auto()

    ROTATE_LEFT = auto()
    ROTATE_RIGHT = auto()

    RESET_CAMERA = auto()