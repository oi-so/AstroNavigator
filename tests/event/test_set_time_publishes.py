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
from astronavigator.event.event_type import EventType



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

    event_bus = EventBus()
    controller = SceneController(scene, event_bus)

    received_event = None

    def callback(event):
        nonlocal received_event
        received_event = event

    event_bus.subscribe(EventType.TIME_CHANGED, callback)

    new_time = Time(datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")))

    controller.set_time(new_time)

    assert received_event is not None
    assert received_event.event_type == EventType.TIME_CHANGED
    assert received_event.payload == new_time