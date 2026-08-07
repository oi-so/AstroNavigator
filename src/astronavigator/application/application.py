from __future__ import annotations


from astronavigator.catalog.catalog_manager import CatalogManager
from astronavigator.catalog.parser.constellation_parser import ConstellationJsonParser
from astronavigator.catalog.parser.hyg_parser import HygParser
from astronavigator.catalog.parser.skyfield_parser import SkyfieldParser
from astronavigator.catalog.provider.debug_catalog_provider import DebugCatalogProvider
from astronavigator.catalog.provider.local_file_provider import LocalFileProvider
from astronavigator.gui.actions.main_actions import MainActions
from astronavigator.input.input_controller import InputController
from astronavigator.rendering.projection.linear_projection import LinearProjection  # noqa: F401
from astronavigator.rendering.projection.horizontal_linear_projection import HorizontalLinearProjection as HorizontalProjection  # noqa: F401
from astronavigator.rendering.projection.projection_manager import ProjectionManager
from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.event.event_bus import EventBus
from astronavigator.sky.position import Position
from astronavigator.catalog.catalog_info import CONSTELLATIONS, EPHEMERIS, HYG


class Application:
    def __init__(self):
        self._scene = Scene()
        self._event_bus = EventBus()
        # self._projection_manager = ProjectionManager(LinearProjection())
        self._projection_manager = ProjectionManager(HorizontalProjection())
        self._scene_controller = SceneController(self._scene, self._event_bus, self._projection_manager)
        self._renderer = Renderer(projection_manager=self._projection_manager)
        self._input_controller = InputController(self._scene_controller)
        self.main_actions = MainActions(self)
        self._catalog_manager = CatalogManager()
        self._load_hyg()
        self._load_constellations()
        self._load_skyfield()


    def _test(self):
        provider = DebugCatalogProvider()
        catalog = provider.load()
        self._scene_controller.add_catalog(catalog)
        self._scene.sky_camera.center = Position(ra_deg=0, dec_deg=0)

    def _load_hyg(self):
        self._catalog_manager.download_catalog(HYG)
        parser = HygParser()
        provider = LocalFileProvider(path=HYG.save_path, parser=parser)
        catalog = provider.load()
        self._scene_controller.add_catalog(catalog)

    def _load_constellations(self):
        self._catalog_manager.download_catalog(CONSTELLATIONS)
        parser = ConstellationJsonParser()
        provider = LocalFileProvider(path=CONSTELLATIONS.save_path, parser=parser)
        catalog = provider.load()
        self._scene_controller.add_constellation_catalog(catalog)

    def _load_skyfield(self):
        self._catalog_manager.download_catalog(EPHEMERIS)
        provider = LocalFileProvider(path=EPHEMERIS.save_path, parser=SkyfieldParser())
        self._scene.skyfield = provider.load()

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