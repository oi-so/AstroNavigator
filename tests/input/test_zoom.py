from unittest.mock import Mock

import pytest

from astronavigator.input.input_controller import InputController


def test_small_wheel_deltas_combine_to_one_notch():
    controller = Mock()
    inputs = InputController(controller)
    for _ in range(120):
        inputs.handle_wheel(1)
    factor = 1.0
    for call in controller.zoom_camera.call_args_list:
        factor *= call.args[0]
    assert factor == pytest.approx(0.9)
    inputs.handle_wheel(-120)
    assert controller.zoom_camera.call_args.args[0] == pytest.approx(1 / 0.9)


def test_zero_wheel_delta_does_not_zoom():
    controller = Mock()
    InputController(controller).handle_wheel(0)
    controller.zoom_camera.assert_not_called()
