from __future__ import annotations

import math
from PySide6.QtCore import QPointF, QSize

from astronavigator.input.input_action import InputAction
from astronavigator.scene.scene_controller import SceneController



MOVE_STEP_DEG = 1.0  # degrees
ZOOM_FACTOR = 0.9  # Zoom in/out factor
PINCH_SENSITIVITY = 2


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


    def handle_wheel(self, delta: float) -> None:
        if delta > 0:
            self._scene_controller.zoom_camera(ZOOM_FACTOR)
        else:
            self._scene_controller.zoom_camera(1 / ZOOM_FACTOR)


    def handle_pinch(self, scale_delta: float) -> None:
        self._scene_controller.zoom_camera(math.exp(-scale_delta * PINCH_SENSITIVITY))

    
    def handle_drag(self, dx: int, dy: int, viewport_size: QSize) -> None:
        camera = self._scene_controller.scene.sky_camera

        deg_per_pixel = camera.fov_deg / viewport_size.width()

        delta_ra = -dx * deg_per_pixel
        delta_dec = dy * deg_per_pixel

        self._scene_controller.move_camera(delta_ra, delta_dec)

    
    def handle_click(self, position: QPointF, viewport_size: QSize) -> None:
        self._scene_controller.select_object_at(position, viewport_size)