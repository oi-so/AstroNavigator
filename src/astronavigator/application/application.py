from __future__ import annotations

from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.event.event_bus import EventBus

from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Star
from astronavigator.sky.object_tree import ObjectType

class Application:
    def __init__(self):
        self._scene = Scene()
        self._event_bus = EventBus()
        self._scene_controller = SceneController(self._scene, self._event_bus)
        self._renderer = Renderer()

        test_star = Star("test", "Test Star", ObjectType.STAR, Position(0, 0), Magnitude(1.0))
        self._scene_controller.add_object(test_star)
        self.scene.sky_camera.center = Position(0, 0)

    
    @property
    def scene(self) -> Scene:
        return self._scene
    
    @property
    def renderer(self) -> Renderer:
        return self._renderer
    
    @property
    def event_bus(self) -> EventBus:
        return self._event_bus
    
    @property
    def scene_controller(self) -> SceneController:
        return self._scene_controller