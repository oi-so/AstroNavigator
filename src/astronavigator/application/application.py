from __future__ import annotations

import math
from pathlib import Path
from dataclasses import replace
import time
from datetime import datetime, timezone
from PySide6.QtCore import QStandardPaths, QTimer


from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.catalog_manager import CatalogManager
from astronavigator.catalog.parser.constellation_parser import ConstellationJsonParser
from astronavigator.catalog.parser.hyg_parser import HygParser
from astronavigator.catalog.parser.omm_csv_parser import OmmCsvParser
from astronavigator.catalog.parser.satellite_magnitude_parser import SatelliteMagnitudeParser
from astronavigator.catalog.parser.skyfield_parser import SkyfieldParser
from astronavigator.catalog.parser.ngc_parser import NGCParser
from astronavigator.catalog.parser.mpc_comet_parser import MpcCometParser
from astronavigator.catalog.provider.debug_catalog_provider import DebugCatalogProvider
from astronavigator.catalog.provider.local_file_provider import LocalFileProvider
from astronavigator.catalog.provider.solar_system_provider import SolarSystemProvider
from astronavigator.event.event_type import EventType
from astronavigator.gui.actions.main_actions import MainActions
from astronavigator.input.input_controller import InputController
from astronavigator.mount.e_zeus.e_zeus2 import EZeus2
from astronavigator.mount.mount import ConnectionState, Mount
from astronavigator.mount.simulator import SimulatorMount
from astronavigator.rendering.projection.stereographic_projection import StereographicProjection
from astronavigator.rendering.projection.projection_manager import ProjectionManager
from astronavigator.rendering.renderer import Renderer
from astronavigator.scene.scene import Scene
from astronavigator.scene.scene_controller import SceneController
from astronavigator.event.event_bus import EventBus
from astronavigator.catalog.catalog_info import CONSTELLATIONS, EPHEMERIS, HYG, OPENNGC_ADDENDUM, OPENNGC_NGC, SATELLITE_MAGNITUDES, VISUAL_SATELLITES_OMM, MPC_COMETS
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.satellite_render_cache import SatelliteRenderCache
from astronavigator.sky.sky_object import Satellite
from astronavigator.tracking.e_zeus_rate_profile_repository import EZeusRateProfileRepository
from astronavigator.tracking.mount_tracking import MountTrackingBackend
from astronavigator.tracking.replayed_target_predictor import ReplayCoordinateMapper
from astronavigator.tracking.simulator_tracking import SimulatorTrackingBackend
from astronavigator.tracking.target_predictor import TargetPredictor
from astronavigator.tracking.tracking_adjustment import TrackingAdjustment
from astronavigator.tracking.tracking_config import TrackingConfig
from astronavigator.tracking.tracking_controller import TrackingController
from astronavigator.tracking.tracking_plan import TrackingPlan
from astronavigator.tracking.tracking_planner import TrackingPlanner
from astronavigator.tracking.tracking_safety_policy import TrackingSafetyContext, TrackingSafetyPolicy, TrackingSafetyResult
from astronavigator.tracking.replayed_target_predictor import ReplayCoordinateMapper, ReplayedTargetPredictor
from astronavigator.tracking.tracking_state import TrackingRunMode, TrackingState
from astronavigator.tracking.tracking_time_provider import SystemUtcTimeProvider, TrackingTimeProvider
from astronavigator.tracking.tracking_time_provider import SimulationTimeProvider
from astronavigator.tracking.target_horizontal_position_calculator import SkyfieldHorizontalPositionCalculator
from astronavigator.tracking.e_zeus_tracking_backend import EZeusTrackingBackend


FPS = 60

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
        # self._load_comets()

        self._satellite_render_cache = SatelliteRenderCache()
        self._satellite_render_cache.snapshot_changed.connect(self._on_satellite_snapshot_changed)

        self._request_satellite_snapshot()

        self._tracking_controller: TrackingController | None = None
        self._tracking_time_provider: TrackingTimeProvider | None = None
        self._tracking_config: TrackingConfig | None = None
        self._tracking_update_accumulator = 0.0
        self._tracking_replay_mapper: ReplayCoordinateMapper | None = None

        config_directory = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppConfigLocation
            )
        )

        self._e_zeus_rate_profile_repository = (
            EZeusRateProfileRepository(config_directory / "e_zeus_rate_profiles.json")
        )

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
        self._catalog_manager.download_catalog(SATELLITE_MAGNITUDES)
        mag_parser = SatelliteMagnitudeParser()
        standard_magnitudes = mag_parser.parse(SATELLITE_MAGNITUDES.save_path)

        self._catalog_manager.download_catalog(VISUAL_SATELLITES_OMM)
        parser = OmmCsvParser(skyfield=self._scene.skyfield, catalog_name="CelesTrak Visual Satellites", standard_magnitudes=standard_magnitudes)
        provider = LocalFileProvider(path=VISUAL_SATELLITES_OMM.save_path, parser=parser)
        catalog = provider.load()
        self._scene_controller.add_catalog(catalog)


    def _load_openngc(self) -> None:
        parser = NGCParser()
        objects_by_id = {}

        for catalog_info in (OPENNGC_NGC, OPENNGC_ADDENDUM):
            self._catalog_manager.download_catalog(catalog_info)
            provider = LocalFileProvider(path=catalog_info.save_path, parser=parser)
            catalog = provider.load()
            for obj in catalog.objects:
                objects_by_id.setdefault(obj.id, obj)

        catalog = Catalog(name="OpenNGC", objects=list(objects_by_id.values()))
        self._scene_controller.add_catalog(catalog)


    def _load_comets(self) -> None:
        skyfield_context = self._scene.skyfield

        if skyfield_context is None:
            raise RuntimeError("Skyfield context is not loaded yet.")

        self._catalog_manager.download_catalog(MPC_COMETS)
        parser = MpcCometParser(skyfield=skyfield_context, catalog_name=MPC_COMETS.name)
        provider = LocalFileProvider(path=MPC_COMETS.save_path, parser=parser)

        catalog = provider.load()
        self._scene_controller.add_catalog(catalog)

    def _update(self):
        current_time = time.monotonic()
        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time

        self._update_scene_time(delta_time)
        self._request_satellite_snapshot()
        self._update_dynamic_tracking(delta_time)
        # print(f"Update: {delta_time:.3f} seconds")

    def _update_scene_time(self, delta_time: float):
        provider = self._tracking_time_provider
        controller = self._tracking_controller
        if provider is not None and controller is not None and controller.is_active and provider.mode is TrackingRunMode.OBSERVATION:
            if self._scene.time.speed != 1.0:
                self._scene_controller.set_time_speed(1.0)
            if self._scene.time.is_paused:
                self._scene_controller.set_time_paused(False)
            self._scene_controller.set_time(provider.get_snapshot().utc)
            return

        self._scene_controller.advance_time(delta_time)

    def _update_dynamic_tracking(self, delta_time: float):
        controller = self._tracking_controller
        config = self._tracking_config

        if controller is None or config is None or not controller.is_active:
            return

        self._tracking_update_accumulator += delta_time
        if self._tracking_update_accumulator < config.prediction_interval:
            return

        tracking_elapsed = self._tracking_update_accumulator
        self._tracking_update_accumulator = 0.0
        previous_state = controller.state

        try:
            update = controller.update(tracking_elapsed, self._create_tracking_safety_context())
        except Exception as e:
            controller.stop()
            self._event_bus.publish(EventType.TRACKING_UPDATED, e)
            self._event_bus.publish(EventType.TRACKING_STATE_CHANGED, TrackingState.FAILED)
            return

        mount_position = controller.mount_position

        provider = self._tracking_time_provider
        mapper = self._tracking_replay_mapper

        if provider is not None and provider.mode is TrackingRunMode.TEST_TRACKING and mapper is not None:
            mount_position = mapper.real_to_simulation(mount_position, datetime.now(timezone.utc))

        self._scene.mount_position = mount_position

        self._event_bus.publish(EventType.TRACKING_UPDATED, update)
        if update.state is not previous_state:
            self._event_bus.publish(EventType.TRACKING_STATE_CHANGED, update.state)
        mount = self._scene.mount
        if mount is not None:
            self._event_bus.publish(EventType.MOUNT_STATE_CHANGED, mount)


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


    @property
    def tracking_controller(self) -> TrackingController | None:
        return self._tracking_controller

    @property
    def tracking_state(self) -> TrackingState:
        if self._tracking_controller is None:
            return TrackingState.IDLE
        return self._tracking_controller.state

    @property
    def e_zeus_rate_profile_repository(self) -> EZeusRateProfileRepository:
        return self._e_zeus_rate_profile_repository

    def start_dynamic_tracking(self, *, run_mode: TrackingRunMode, config: TrackingConfig, adjustment: TrackingAdjustment) -> tuple[TrackingPlan, TrackingSafetyResult]:
        target = self._scene.selection.selected
        mount = self._scene.mount

        if target is None:
            raise RuntimeError("No target selected for tracking.")
        if not target.is_dynamic:
            raise RuntimeError("Selected target is not dynamic and cannot be tracked.")

        if mount is None or not mount.is_connected:
            raise RuntimeError("Mount is not connected for tracking.")

        skyfield_context = self._scene.skyfield
        if skyfield_context is None:
            raise RuntimeError("Skyfield context is not loaded yet.")

        if self._tracking_controller is not None and self._tracking_controller.is_active:
            raise RuntimeError("Dynamic tracking is already active.")

        if run_mode is TrackingRunMode.OBSERVATION:
            time_provider = SystemUtcTimeProvider()
            self._scene_controller.set_time_speed(1.0)
            self._scene_controller.set_time_paused(False)
            self._scene_controller.set_time(time_provider.get_snapshot().utc)
        elif run_mode is TrackingRunMode.TEST_TRACKING:
            if not isinstance(mount, EZeus2):
                raise RuntimeError("Test tracking mode is only available for E-ZEUS II mount.")

            if not math.isclose(self._scene.time.speed, 1.0, rel_tol=1e-9):
                raise RuntimeError("Test tracking mode requires Scene time speed to be 1.0.")

            if self._scene.time.is_paused:
                raise RuntimeError("Test tracking mode requires Scene time to be running (not paused).")

            time_provider = SimulationTimeProvider(lambda: self._scene.time, TrackingRunMode.TEST_TRACKING)
        else:
            time_provider = SimulationTimeProvider(lambda: self._scene.time, TrackingRunMode.REHEARSAL)

        source_predictor = TargetPredictor()
        horizontal_calculator = SkyfieldHorizontalPositionCalculator(skyfield_context)
        planner = TrackingPlanner(source_predictor, horizontal_calculator)
        plan = planner.create_plan(target, self._scene.observer, time_provider, config)

        tracking_predictor = source_predictor
        replay_mapper: ReplayCoordinateMapper | None = None

        if run_mode is TrackingRunMode.TEST_TRACKING:
            simulation_anchor_utc = time_provider.get_snapshot().utc
            real_anchor_utc = datetime.now(timezone.utc)

            replay_mapper = ReplayCoordinateMapper(skyfield_context, self._scene.object_index, simulation_anchor_utc, real_anchor_utc)
            tracking_predictor = ReplayedTargetPredictor(replay_mapper, source_predictor)

            mapped_preposition = tracking_predictor.predict(
                target, self._scene.observer, plan.start_time_utc, config.prediction_horizon
            ).current_position
            plan = replace(plan, preposition=mapped_preposition)

        backend = self._create_tracking_backend(mount, run_mode, config)
        controller = TrackingController(tracking_predictor, backend, time_provider, TrackingSafetyPolicy())
        controller.set_adjustment(adjustment)

        safety_result = controller.prepare(
            target=target,
            observer=self._scene.observer,
            plan=plan,
            config=config,
            safety_context=self._create_tracking_safety_context(run_mode),
        )

        if safety_result.can_start:
            self._tracking_controller = controller
            self._tracking_time_provider = time_provider
            self._tracking_config = config
            self._tracking_replay_mapper = replay_mapper
            self._tracking_update_accumulator = 0.0

        self._event_bus.publish(EventType.TRACKING_STATE_CHANGED, controller.state)

        return plan, safety_result


    def stop_dynamic_tracking(self):
        controller = self._tracking_controller
        if controller is None:
            return 
        controller.stop()
        self._tracking_replay_mapper = None
        self._event_bus.publish(EventType.TRACKING_STATE_CHANGED, controller.state)


    def set_tracking_adjustment(self, adjustment: TrackingAdjustment):
        controller = self._tracking_controller
        if controller is None:
            return
        controller.set_adjustment(adjustment)

    def _create_tracking_safety_context(self, run_mode: TrackingRunMode | None = None) -> TrackingSafetyContext:
        mount = self._scene.mount
        is_simulator = isinstance(mount, SimulatorMount) if mount is not None else False
        if run_mode is None:
            provider = self._tracking_time_provider
            run_mode = provider.mode if provider is not None else TrackingRunMode.OBSERVATION

        mount_synchronized = mount is not None and (is_simulator or bool(getattr(mount, "is_synced", True)))

        return TrackingSafetyContext(
            run_mode=run_mode,
            is_real_mount=mount is not None and not is_simulator,
            mount_connected=mount is not None and mount.is_connected,
            mount_synchronized=mount_synchronized,
            communication_healthy=mount is not None and mount.state is not ConnectionState.ERROR,
            collision_risk=False,
            mount_limit_reached=False,
            time_rate=self._scene.time.speed,
            time_paused=self._scene.time.is_paused
        )



    def _create_tracking_backend(self, mount: Mount, run_mode: TrackingRunMode, config: TrackingConfig) -> MountTrackingBackend:
        if isinstance(mount, SimulatorMount):
            if run_mode is TrackingRunMode.TEST_TRACKING:
                raise RuntimeError("Simulator mount does not support test tracking mode.")
            return SimulatorTrackingBackend(mount)

        if isinstance(mount, EZeus2):
            if run_mode not in (TrackingRunMode.OBSERVATION, TrackingRunMode.TEST_TRACKING):
                raise RuntimeError(f"E-ZEUS II mount does not support run mode: {run_mode}")

            profile_id = config.rate_profile_id
            if profile_id is None:
                raise RuntimeError("E-ZEUS IIレートプロファイルを選択してください。")

            profile = self._e_zeus_rate_profile_repository.get_profile(profile_id)
            if profile is None:
                raise RuntimeError("選択されたE-ZEUS IIレートプロファイルが見つかりません。")

            return EZeusTrackingBackend(
                mount=mount,
                rate_profile=profile,
                control_interval_sec=(
                    config.prediction_interval
                ),
            )

        raise RuntimeError(
            f"{type(mount).__name__} はまだ動的追尾に対応していません。"
        )


    def _request_satellite_snapshot(self):
        objects = self._scene.object_index.find_dynamic_by_type(ObjectType.SATELLITE)
        satellites = tuple(obj for obj in objects if isinstance(obj, Satellite))

        self._satellite_render_cache.request_update(
            time=self._scene.time,
            observer=self._scene.observer,
            satellites=satellites,
        )

    def _on_satellite_snapshot_changed(self, snapshot: SatelliteRenderSnapshot):
        self._scene.satellite_render_snapshot = snapshot
        # self._event_bus.publish(EventType.SCENE_UPDATED, snapshot)