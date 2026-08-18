from __future__ import annotations

from datetime import datetime, timedelta, timezone

from astronavigator.mount.simulator import (
    SimulatorMount,
    SimulatorMountSettings,
)
from astronavigator.scene.observer import Observer
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Star
from astronavigator.tracking.simulator_tracking import (
    SimulatorTrackingBackend,
)
from astronavigator.tracking.target_predictor import TargetPredictor
from astronavigator.tracking.tracking_adjustment import (
    TrackingAdjustment,
)
from astronavigator.tracking.tracking_config import TrackingConfig
from astronavigator.tracking.tracking_controller import (
    TrackingController,
)
from astronavigator.tracking.tracking_plan import TrackingPlan
from astronavigator.tracking.tracking_safety_policy import (
    TrackingSafetyContext,
    TrackingSafetyPolicy,
)
from astronavigator.tracking.tracking_state import (
    TrackingPlanStatus,
    TrackingRunMode,
    TrackingState,
)
from astronavigator.tracking.tracking_time_provider import (
    TrackingTimeProvider,
    TrackingTimeSnapshot,
)
from astronavigator.mount.slew_path import PierSide


class MutableTimeProvider(TrackingTimeProvider):
    def __init__(self, current_time: datetime) -> None:
        self.current_time = current_time
        self.rate = 1.0

    @property
    def mode(self) -> TrackingRunMode:
        return TrackingRunMode.REHEARSAL

    def get_snapshot(self) -> TrackingTimeSnapshot:
        return TrackingTimeSnapshot(
            utc=self.current_time,
            mode=self.mode,
            rate=self.rate,
            is_paused=self.rate == 0.0,
        )


def create_target() -> Star:
    return Star(
        id="test:star",
        name="Test Star",
        object_type=ObjectType.STAR,
        hip=None,
        _position=Position(100.0, 20.0),
        _magnitude=Magnitude(1.0),
    )


def create_plan(
    start_time: datetime,
) -> TrackingPlan:
    return TrackingPlan(
        target_id="test:star",
        status=TrackingPlanStatus.READY,
        start_time_utc=start_time,
        end_time_utc=start_time + timedelta(seconds=10.0),
        initial_pier_side=PierSide.UNKNOWN,
        preposition=Position(100.0, 20.0),
        maximum_required_ra_rate_deg_per_sec=0.0,
        maximum_required_dec_rate_deg_per_sec=0.0,
        requires_meridian_flip=False,
        meridian_flip_time_utc=None,
        rate_profile_id=None,
    )


def create_context() -> TrackingSafetyContext:
    return TrackingSafetyContext(
        run_mode=TrackingRunMode.REHEARSAL,
        is_real_mount=False,
        mount_connected=True,
        mount_synchronized=True,
        communication_healthy=True,
    )


def test_controller_waits_until_start_time() -> None:
    start_time = datetime(
        2026,
        8,
        19,
        12,
        0,
        tzinfo=timezone.utc,
    )
    provider = MutableTimeProvider(
        start_time - timedelta(seconds=1.0)
    )

    mount = SimulatorMount()
    mount.connect()

    backend = SimulatorTrackingBackend(mount)
    controller = TrackingController(
        predictor=TargetPredictor(),
        backend=backend,
        time_provider=provider,
        safety_policy=TrackingSafetyPolicy(),
    )

    controller.prepare(
        target=create_target(),
        observer=Observer.default(),
        plan=create_plan(start_time),
        config=TrackingConfig(),
        safety_context=create_context(),
    )

    result = controller.update(0.1, create_context())

    assert result.state is TrackingState.WAITING
    assert not backend.is_active


def test_gui_ra_adjustment_moves_mount() -> None:
    start_time = datetime(
        2026,
        8,
        19,
        12,
        0,
        tzinfo=timezone.utc,
    )
    provider = MutableTimeProvider(start_time)

    mount = SimulatorMount(
        settings=SimulatorMountSettings(
            maximum_ra_rate_deg_per_sec=2.0,
            maximum_dec_rate_deg_per_sec=2.0,
        )
    )
    mount.connect()

    backend = SimulatorTrackingBackend(mount)
    controller = TrackingController(
        predictor=TargetPredictor(),
        backend=backend,
        time_provider=provider,
        safety_policy=TrackingSafetyPolicy(),
    )

    controller.prepare(
        target=create_target(),
        observer=Observer.default(),
        plan=create_plan(start_time),
        config=TrackingConfig(),
        safety_context=create_context(),
    )

    controller.set_adjustment(
        TrackingAdjustment(
            ra_offset_arcsec=3600.0,
        )
    )

    result = controller.update(1.0, create_context())

    assert result.state is TrackingState.TRACKING
    assert result.command is not None
    assert result.command.applied_ra_rate_deg_per_sec > 0.0
    assert mount.position.ra_deg > 100.0


def test_communication_error_stops_tracking() -> None:
    start_time = datetime(
        2026,
        8,
        19,
        12,
        0,
        tzinfo=timezone.utc,
    )
    provider = MutableTimeProvider(start_time)

    mount = SimulatorMount()
    mount.connect()

    backend = SimulatorTrackingBackend(mount)
    controller = TrackingController(
        predictor=TargetPredictor(),
        backend=backend,
        time_provider=provider,
        safety_policy=TrackingSafetyPolicy(),
    )

    controller.prepare(
        target=create_target(),
        observer=Observer.default(),
        plan=create_plan(start_time),
        config=TrackingConfig(),
        safety_context=create_context(),
    )

    controller.update(0.1, create_context())

    error_context = TrackingSafetyContext(
        run_mode=TrackingRunMode.REHEARSAL,
        is_real_mount=False,
        mount_connected=True,
        mount_synchronized=True,
        communication_healthy=False,
    )

    result = controller.update(0.1, error_context)

    assert result.state is TrackingState.FAILED
    assert not backend.is_active