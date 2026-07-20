from datetime import datetime
from zoneinfo import ZoneInfo

from astronavigator.event.event_bus import EventBus
from astronavigator.scene.observer import Observer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.scene.time import Time
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import Star
from astronavigator.sky.position import Position
from astronavigator.sky.magnitude import Magnitude


def test_set_time():
    scene = Scene()

    controller = SceneController(scene, EventBus())

    new_time = Time(datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")))

    controller.set_time(new_time)

    assert controller.scene.time == new_time


def test_set_observer():
    scene = Scene()

    controller = SceneController(scene, EventBus())

    new_observer = Observer(35.0, 139.0, 40, ZoneInfo("Asia/Tokyo"))

    controller.set_observer(new_observer)

    assert controller.scene.observer == new_observer


def test_select_object():
    scene = Scene()

    controller = SceneController(scene, EventBus())

    new_sky_object = Star("test", "testObject", ObjectType.STAR, Position(0.0, 0.0), Magnitude(1.0))

    controller.select_object(new_sky_object)

    assert controller.scene.selection.selected == new_sky_object


def test_clear_selection():
    scene = Scene()

    controller = SceneController(scene, EventBus())

    new_sky_object = Star("test", "testObject", ObjectType.STAR, Position(0.0, 0.0), Magnitude(1.0))

    controller.select_object(new_sky_object)

    assert controller.scene.selection.selected == new_sky_object

    controller.clear_selection()

    assert controller.scene.selection.selected is None

def test_add_and_remove_object():
    scene = Scene()

    controller = SceneController(scene, EventBus())

    new_sky_object = Star("test", "testObject", ObjectType.STAR, Position(0.0, 0.0), Magnitude(1.0))

    controller.add_object(new_sky_object)

    assert new_sky_object in controller.scene.objects

    controller.remove_object(new_sky_object)

    assert new_sky_object not in controller.scene.objects