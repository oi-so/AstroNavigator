from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar

import pytest

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import (
    HorizontalPosition,
    Position,
)
from astronavigator.sky.sky_object import SkyObject
from astronavigator.tracking import (
    SystemUtcTimeProvider,
    TargetHorizontalPositionCalculator,
    TargetPredictor,
    TrackingConfig,
    TrackingPlanStatus,
    TrackingPlanner,
    TrackingPlannerSettings,
)


@dataclass(slots=True)
class LinearSkyObject(SkyObject):
    reference_time_utc: datetime
    reference_ra_deg: float
    reference_dec_deg: float

    ra_rate_deg_per_sec: float
    dec_rate_deg_per_sec: float

    is_dynamic: ClassVar[bool] = True

    def get_position(
        self,
        time: Time | None = None,
        observer: Observer | None = None,
    ) -> Position:
        if time is None:
            raise ValueError("time is required.")

        elapsed_sec = (
            time.utc - self.reference_time_utc
        ).total_seconds()

        return Position(
            ra_deg=(
                self.reference_ra_deg
                + self.ra_rate_deg_per_sec * elapsed_sec
            ),
            dec_deg=(
                self.reference_dec_deg
                + self.dec_rate_deg_per_sec * elapsed_sec
            ),
        ).normalized()

    def get_magnitude(
        self,
        time: Time | None = None,
        observer: Observer | None = None,
    ) -> Magnitude:
        return Magnitude(0.0)


class PassHorizontalCalculator(
    TargetHorizontalPositionCalculator
):
    def __init__(
        self,
        reference_time_utc: datetime,
    ) -> None:
        self._reference_time_utc = reference_time_utc

    def calculate(
        self,
        position: Position,
        time_utc: datetime,
        observer: Observer,
    ) -> HorizontalPosition:
        elapsed_sec = (
            time_utc - self._reference_time_utc
        ).total_seconds()

        altitude_deg = 20.0 - abs(elapsed_sec - 20.0)

        return HorizontalPosition(
            azimuth_deg=180.0,
            altitude_deg=altitude_deg,
        )


class ConstantHorizontalCalculator(
    TargetHorizontalPositionCalculator
):
    def __init__(self, altitude_deg: float) -> None:
        self._altitude_deg = altitude_deg

    def calculate(
        self,
        position: Position,
        time_utc: datetime,
        observer: Observer,
    ) -> HorizontalPosition:
        return HorizontalPosition(
            azimuth_deg=180.0,
            altitude_deg=self._altitude_deg,
        )


def create_target(
    reference_time_utc: datetime,
) -> LinearSkyObject:
    return LinearSkyObject(
        id="test:pass",
        name="Test Pass",
        object_type=ObjectType.SATELLITE,
        hip=None,
        reference_time_utc=reference_time_utc,
        reference_ra_deg=0.0,
        reference_dec_deg=0.0,
        ra_rate_deg_per_sec=2.0,
        dec_rate_deg_per_sec=0.5,
    )


def create_provider(
    current_time_utc: datetime,
) -> SystemUtcTimeProvider:
    return SystemUtcTimeProvider(
        now_function=lambda: current_time_utc,
    )


def create_settings() -> TrackingPlannerSettings:
    return TrackingPlannerSettings(
        search_horizon_sec=60.0,
        coarse_search_interval_sec=5.0,
        crossing_precision_sec=0.01,
        motion_sample_interval_sec=1.0,
        max_motion_samples=100,
    )


def test_planner_finds_entry_and_exit_crossings() -> None:
    start_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    planner = TrackingPlanner(
        predictor=TargetPredictor(),
        horizontal_calculator=PassHorizontalCalculator(
            start_time
        ),
        settings=create_settings(),
    )

    plan = planner.create_plan(
        target=create_target(start_time),
        observer=Observer.default(),
        time_provider=create_provider(start_time),
        config=TrackingConfig(
            entry_altitude_deg=10.5,
            exit_altitude_deg=10.0,
            prediction_horizon=1.0,
            rate_profile_id="test-profile",
        ),
    )

    assert plan.status is TrackingPlanStatus.READY

    assert (
        plan.start_time_utc - start_time
    ).total_seconds() == pytest.approx(
        10.5,
        abs=0.02,
    )

    assert (
        plan.end_time_utc - start_time
    ).total_seconds() == pytest.approx(
        30.0,
        abs=0.02,
    )

    assert (
        plan.maximum_required_ra_rate_deg_per_sec
        == pytest.approx(2.0)
    )
    assert (
        plan.maximum_required_dec_rate_deg_per_sec
        == pytest.approx(0.5)
    )


def test_planner_uses_current_time_when_already_visible() -> None:
    reference_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )
    current_time = reference_time.replace(second=15)

    planner = TrackingPlanner(
        predictor=TargetPredictor(),
        horizontal_calculator=PassHorizontalCalculator(
            reference_time
        ),
        settings=create_settings(),
    )

    plan = planner.create_plan(
        target=create_target(reference_time),
        observer=Observer.default(),
        time_provider=create_provider(current_time),
        config=TrackingConfig(
            rate_profile_id="test-profile",
        ),
    )

    assert plan.status is TrackingPlanStatus.READY
    assert plan.start_time_utc == current_time
    assert "すでに開始高度以上" in plan.warnings[0]


def test_planner_blocks_target_that_never_rises() -> None:
    start_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    planner = TrackingPlanner(
        predictor=TargetPredictor(),
        horizontal_calculator=(
            ConstantHorizontalCalculator(-5.0)
        ),
        settings=create_settings(),
    )

    plan = planner.create_plan(
        target=create_target(start_time),
        observer=Observer.default(),
        time_provider=create_provider(start_time),
        config=TrackingConfig(
            rate_profile_id="test-profile",
        ),
    )

    assert plan.status is TrackingPlanStatus.BLOCKED
    assert plan.blocked_reason is not None


def test_planner_uses_maximum_session_time() -> None:
    start_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    planner = TrackingPlanner(
        predictor=TargetPredictor(),
        horizontal_calculator=(
            ConstantHorizontalCalculator(30.0)
        ),
        settings=create_settings(),
    )

    plan = planner.create_plan(
        target=create_target(start_time),
        observer=Observer.default(),
        time_provider=create_provider(start_time),
        config=TrackingConfig(
            max_session_sec=20.0,
            rate_profile_id="test-profile",
        ),
    )

    assert plan.status is TrackingPlanStatus.READY
    assert plan.end_time_utc is not None

    assert (
        plan.end_time_utc - start_time
    ).total_seconds() == pytest.approx(20.0)

    assert "最大追尾時間" in plan.warnings[1]


def test_planner_settings_reject_invalid_values() -> None:
    with pytest.raises(ValueError):
        TrackingPlannerSettings(
            coarse_search_interval_sec=0.0,
        )