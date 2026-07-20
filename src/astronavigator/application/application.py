from __future__ import annotations

from astronavigator.catalog.debug_catalog_provider import DebugCatalogProvider
from astronavigator.input.input_controller import InputController
from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.event.event_bus import EventBus

from astronavigator.sky.position import Position

from astronavigator.debug.stars import create_test_stars


class Application:
    def __init__(self):
        self._scene = Scene()
        self._event_bus = EventBus()
        self._scene_controller = SceneController(self._scene, self._event_bus)
        self._renderer = Renderer()
        self._input_controller = InputController(self._scene_controller)

        self._test()  # テスト用の星を追加

    def _test(self):
        provider = DebugCatalogProvider()
        catalog = provider.load()
        self._scene_controller.load_catalog(catalog)

        self._scene.sky_camera.center = Position(ra_deg=0, dec_deg=0)


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
    
    @property
    def input_controller(self) -> InputController:
        return self._input_controller