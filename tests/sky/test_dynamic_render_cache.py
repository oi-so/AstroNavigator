from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QPointF, QRect

from astronavigator.event.event_bus import EventBus
from astronavigator.layer.object_layer import ObjectLayer
from astronavigator.layer.selection_layer import SelectionLayer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.sky.dynamic_render_cache import (
    DynamicRenderCache,
    DynamicRenderState,
    interpolate_position,
)
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Comet


class MovingObject:
    id = "moving"
    is_dynamic = True

    def __init__(self, start):
        self.start = start
        self.calls = []

    def get_position(self, time, observer):
        self.calls.append(time.utc)
        seconds = (time.utc - self.start).total_seconds()
        return Position((359 + seconds) % 360, 0)

    def get_magnitude(self, time, observer):
        return Magnitude(5)


def test_every_frame_moves_within_interval_without_recalculating_or_delaying():
    scene = Scene()
    scene.time.utc = datetime(2026, 9, 9, tzinfo=timezone.utc)
    obj = MovingObject(scene.time.utc)
    scene.selection.selected = obj
    cache = DynamicRenderCache()
    first = cache.calculate(scene)[obj.id]
    assert first.position.ra_deg == 359
    for _ in range(5):
        scene.time.advance(0.1)
        state = cache.calculate(scene)[obj.id]
        assert state.position.ra_deg > first.position.ra_deg
        first = state
    assert state.position.ra_deg == pytest.approx(359.5)
    assert len(obj.calls) == 2


@pytest.mark.parametrize("speed", [1_000_000, -1_000_000])
def test_fast_time_uses_current_position_and_focus_matches_selection(speed):
    scene = Scene()
    obj = MovingObject(scene.time.utc)
    scene.selection.selected = scene.focus.target = obj
    scene.time.speed = speed
    controller = SceneController(scene, EventBus(), Mock())
    cache = DynamicRenderCache()
    for _ in range(3):
        controller.advance_time(0.016)
        states = cache.calculate(scene)
        controller.set_dynamic_render_states(states)
        assert obj.calls[-1] == scene.time.utc
        assert scene.sky_camera.center == states[obj.id].position
    assert len(obj.calls) == 3


def test_context_change_and_time_reversal_invalidate_interpolation():
    scene = Scene()
    obj = MovingObject(scene.time.utc)
    scene.selection.selected = obj
    cache = DynamicRenderCache()
    cache.calculate(scene)
    scene.observer.latitude += 1
    cache.calculate(scene)
    assert len(obj.calls) == 4
    scene.time.revision += 1
    cache.calculate(scene)
    assert len(obj.calls) == 6
    scene.time.speed = -1
    cache.calculate(scene)
    assert scene.time.utc - timedelta(seconds=1) <= obj.calls[-1] < scene.time.utc


def test_ra_wrap_and_pole_interpolation_remain_on_short_path():
    assert interpolate_position(
        Position(359, 0), Position(1, 0), 0.5
    ).ra_deg == pytest.approx(0)
    assert interpolate_position(
        Position(0, 89), Position(180, 89), 0.5
    ).dec_deg == pytest.approx(90)


def test_marker_and_body_use_same_position_during_zoom_without_snapshot():
    scene = Scene()
    comet = Mock(spec=Comet)
    comet.id = "comet"
    comet.object_type = ObjectType.COMET
    scene.selection.selected = comet
    scene.dynamic_render_states[comet.id] = DynamicRenderState(
        Position(12, 34), Magnitude(5)
    )
    layer = ObjectLayer()
    layer._draw_object = Mock()
    projection = Mock()
    projection.project.return_value = QPointF(10, 20)
    context = SimpleNamespace(
        scene=scene,
        projection=projection,
        projection_context=Mock(),
        viewport=QRect(0, 0, 800, 600),
        painter=Mock(),
    )
    for fov in (10, 1, 0.1):
        scene.sky_camera.fov_deg = fov
        layer._render_object(comet, 11, context.viewport.size(), context)
        SelectionLayer().render(context)
        assert projection.project.call_args.args[0] == Position(12, 34)
        assert (
            layer._draw_object.call_args.args[1]
            == context.painter.drawEllipse.call_args.args[0]
        )
    comet.get_position.assert_not_called()
