from __future__ import annotations

import time
from PySide6.QtCore import QTimer


from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.catalog_manager import CatalogManager
from astronavigator.catalog.parser.constellation_parser import ConstellationJsonParser
from astronavigator.catalog.parser.hyg_parser import HygParser
from astronavigator.catalog.parser.omm_csv_parser import OmmCsvParser
from astronavigator.catalog.parser.skyfield_parser import SkyfieldParser
from astronavigator.catalog.parser.ngc_parser import NGCParser
from astronavigator.catalog.provider.debug_catalog_provider import DebugCatalogProvider
from astronavigator.catalog.provider.local_file_provider import LocalFileProvider
from astronavigator.catalog.provider.solar_system_provider import SolarSystemProvider
from astronavigator.gui.actions.main_actions import MainActions
from astronavigator.input.input_controller import InputController
from astronavigator.rendering.projection.stereographic_projection import StereographicProjection
from astronavigator.rendering.projection.projection_manager import ProjectionManager
from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.event.event_bus import EventBus
from astronavigator.catalog.catalog_info import CONSTELLATIONS, EPHEMERIS, HYG, OPENNGC_ADDENDUM, OPENNGC_NGC, VISUAL_SATELLITES_OMM


FPS = 30

class Application:
    def __init__(self):
        self._scene = Scene()
        self._event_bus = EventBus()
        self._projection_manager = ProjectionManager(StereographicProjection())
        self._scene_controller = SceneController(self._scene, self._event_bus, self._projection_manager)
        self._renderer = Renderer(projection_manager=self._projection_manager)
        self._input_controller = InputController(self._scene_controller)
        self.main_actions = MainActions(self)
        self._catalog_manager = CatalogManager()
        self._load_hyg()
        self._load_constellations()
        self._load_skyfield()
        self._load_solar_system()
        self._load_satellites()
        self._load_openngc()

        self._last_update_time = time.monotonic()
        self._update_timer = QTimer()
        self._update_timer.setInterval(1000 // FPS)
        self._update_timer.timeout.connect(self._update)
        self._update_timer.start()


    def _test(self):
        provider = DebugCatalogProvider()
        catalog = provider.load()
        self._scene_controller.add_catalog(catalog)

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

    def _load_solar_system(self):
        context = self._scene.skyfield
        if context is None:
            raise RuntimeError("Skyfield context is not loaded yet.")
        provider = SolarSystemProvider(context)
        catalog = provider.load()
        self._scene_controller.add_catalog(catalog)

    def _load_satellites(self):
        if self._scene.skyfield is None:
            raise RuntimeError("Skyfield context is not loaded yet.")
        self._catalog_manager.download_catalog(VISUAL_SATELLITES_OMM)
        parser = OmmCsvParser(skyfield=self._scene.skyfield, catalog_name="CelesTrak Visual Satellites")
        provider = LocalFileProvider(path=VISUAL_SATELLITES_OMM.save_path, parser=parser)
        catalog = provider.load()
        self._scene_controller.add_catalog(catalog)


    def _load_openngc(self) -> None:
        started_at = time.perf_counter()

        parser = NGCParser()
        objects_by_id = {}

        for catalog_info in (OPENNGC_NGC, OPENNGC_ADDENDUM):
            self._catalog_manager.download_catalog(catalog_info)
            provider = LocalFileProvider(path=catalog_info.save_path, parser=parser)
            catalog = provider.load()
            for obj in catalog.objects:
                objects_by_id.setdefault(obj.id, obj)

        catalog = Catalog(name="OpenNGC", objects=list(objects_by_id.values()))

        # parsed_at = time.perf_counter()
        self._scene_controller.add_catalog(catalog)
        # completed_at = time.perf_counter()
        # print(f"OpenNGC loaded in {completed_at - started_at:.3f}s (parsed in {parsed_at - started_at:.3f}s)")


    def _update(self):
        current_time = time.monotonic()
        delta_time = current_time - self._last_update_time
        # print(f"[update] delta_time={delta_time:.4f}s")
        self._last_update_time = current_time

        self._scene_controller.advance_time(delta_time)

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