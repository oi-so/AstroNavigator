from __future__ import annotations

from astronavigator.scene.scene import Scene
from astronavigator.event.event_bus import EventBus


class SceneController:
    def __init__(self, scene: Scene, event_bus: EventBus):
        self.scene = scene
        self.event_bus = event_bus

    def set_time(self):
        pass

    def set_observer(self):
        pass

    def add_object(self, obj):
        pass

    def remove_object(self, obj):
        pass

    def select_object(self, obj):
        pass

    def clear_selection(self):
        pass

    def set_focus(self, obj):
        pass

    def clear_focus(self):
        pass