from __future__ import annotations


from astronavigator.event.event_type import EventType
from astronavigator.scene.scene import Scene
from astronavigator.event.event_bus import EventBus
from astronavigator.sky.sky_object import SkyObject
from astronavigator.scene.time import Time


class SceneController:
    def __init__(self, scene: Scene, event_bus: EventBus):
        self._scene = scene
        self._event_bus = event_bus

    @property
    def scene(self) -> Scene:
        return self._scene

    def set_time(self, time: Time) -> None:
        self._scene.time = time
        self._event_bus.publish(EventType.TIME_CHANGED, time)

    def set_observer(self, observer: SkyObject) -> None:
        pass

    def add_object(self, sky_object: SkyObject) -> None:
        pass

    def remove_object(self, sky_object: SkyObject) -> None:
        pass

    def select_object(self, sky_object: SkyObject) -> None:
        pass

    def clear_selection(self) -> None:
        pass

    def set_focus(self, sky_object: SkyObject) -> None:
        pass

    def clear_focus(self) -> None:
        pass
