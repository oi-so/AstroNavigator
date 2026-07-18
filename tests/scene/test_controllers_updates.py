from datetime import datetime
from zoneinfo import ZoneInfo

from astronavigator.event.event_bus import EventBus
from astronavigator.scene.observer import Observer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.scene.time import Time



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