from astronavigator.input.input_action import InputAction
from astronavigator.scene.scene_controller import SceneController



MOVE_STEP_DEG = 1.0  # degrees
ZOOM_FACTOR = 0.9  # Zoom in/out factor


class InputController:
    def __init__(self, scene_controller: SceneController):
        self._scene_controller = scene_controller

    def handle_action(self, action: InputAction) -> None:
        match action:
            case InputAction.MOVE_UP:
                self._scene_controller.move_camera(0, MOVE_STEP_DEG)
            case InputAction.MOVE_DOWN:
                self._scene_controller.move_camera(0, -MOVE_STEP_DEG)
            case InputAction.MOVE_LEFT:
                self._scene_controller.move_camera(-MOVE_STEP_DEG, 0)
            case InputAction.MOVE_RIGHT:
                self._scene_controller.move_camera(MOVE_STEP_DEG, 0)
            case InputAction.ZOOM_IN:
                self._scene_controller.zoom_camera(ZOOM_FACTOR)
            case InputAction.ZOOM_OUT:
                self._scene_controller.zoom_camera(1 / ZOOM_FACTOR)
            case InputAction.RESET_CAMERA:
                raise NotImplementedError("Reset camera action is not implemented yet.")
            case _:
                raise ValueError(f"Unhandled action: {action}")