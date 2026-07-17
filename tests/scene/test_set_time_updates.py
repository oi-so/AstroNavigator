from datetime import datetime
from zoneinfo import ZoneInfo

from astronavigator.event.event_bus import EventBus
from astronavigator.layer.layer_manager import LayerManager
from astronavigator.scene.focus import Focus
from astronavigator.scene.observer import Observer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.scene.selection import Selection
from astronavigator.scene.sky_camera import SkyCamera
from astronavigator.scene.time import Time



def test_set_time():
    scene = Scene(
        Observer(36, 139, 100, ZoneInfo("Asia/Tokyo")),
        Time(datetime(2023, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))), 
        [], 
        Selection(), 
        Focus(), 
        LayerManager(), 
        SkyCamera()
    )

    controller = SceneController(scene, EventBus())

    new_time = Time(datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")))

    controller.set_time(new_time)

    assert controller.scene.time == new_time