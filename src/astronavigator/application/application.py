from __future__ import annotations

from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.event.event_bus import EventBus

class Application:
    def __init__(self):
        self._scene = Scene()
        self._event_bus = EventBus()
        self._scene_controller = SceneController(self._scene, self._event_bus)

    
    @property
    def scene(self) -> Scene:
        return self._scene
    
    @property
    def event_bus(self) -> EventBus:
        return self._event_bus
    
    @property
    def scene_controller(self) -> SceneController:
        return self._scene_controller