from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import pytest

from astronavigator.mount.mount import Axis
from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.position import Position
from astronavigator.tracking.tracking_adjustment import TrackingAdjustment
from astronavigator.tracking.tracking_config import TrackingConfig
from astronavigator.tracking.tracking_plan import RateLimitWarning, TrackingPlan
from astronavigator.tracking.tracking_state import TrackingPlanStatus


def create_plan(
    *,
    status: TrackingPlanStatus = TrackingPlanStatus.READY,
    requires_meridian_flip: bool = False,
    meridian_flip_time_utc: datetime | None = None,
    rate_limit_warnings: tuple[RateLimitWarning, ...] = (),
    blocked_reason: str | None = None,
) -> TrackingPlan:
    start_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return TrackingPlan(
        target_id="satellite:iss",
        status=status,
        start_time_utc=start_time,
        end_time_utc=start_time + timedelta(minutes=5),
        initial_pier_side=PierSide.EAST,
        preposition=Position(
            ra_deg=120.0,
            dec_deg=30.0,
        ),
        maximum_required_ra_rate_deg_per_sec=0.5,
        maximum_required_dec_rate_deg_per_sec=0.3,
        requires_meridian_flip=requires_meridian_flip,
        meridian_flip_time_utc=meridian_flip_time_utc,
        rate_profile_id="simulator-default",
        rate_limit_warnings=rate_limit_warnings,
        blocked_reason=blocked_reason,
    )


def test_tracking_config_defaults() -> None:
    config = TrackingConfig()

    assert config.entry_altitude_deg == 10.5
    assert config.exit_altitude_deg == 10.0
    assert config.prediction_interval == 0.2


def test_tracking_config_rejects_invalid_altitude_order() -> None:
    with pytest.raises(ValueError):
        TrackingConfig(
            entry_altitude_deg=10.0,
            exit_altitude_deg=15.0,
        )


def test_tracking_config_rejects_short_prediction_horizon() -> None:
    with pytest.raises(ValueError):
        TrackingConfig(
            prediction_interval=1.0,
            prediction_horizon=0.5,
        )


def test_tracking_adjustment_is_immutable() -> None:
    adjustment = TrackingAdjustment()

    with pytest.raises(FrozenInstanceError):
        adjustment.ra_offset_arcsec = 10.0


def test_tracking_adjustment_can_be_replaced() -> None:
    adjustment = TrackingAdjustment()

    updated = replace(
        adjustment,
        ra_offset_arcsec=10.0,
        manual_time_offset_sec=0.2,
    )

    assert adjustment.ra_offset_arcsec == 0.0
    assert updated.ra_offset_arcsec == 10.0
    assert updated.manual_time_offset_sec == 0.2


def test_tracking_plan_normalizes_time_to_utc() -> None:
    japan_timezone = timezone(timedelta(hours=9))
    start_time = datetime(
        2026,
        8,
        18,
        21,
        0,
        tzinfo=japan_timezone,
    )

    plan = TrackingPlan(
        target_id="satellite:iss",
        status=TrackingPlanStatus.READY,
        start_time_utc=start_time,
        end_time_utc=None,
        initial_pier_side=PierSide.EAST,
        preposition=Position(120.0, 30.0),
        maximum_required_ra_rate_deg_per_sec=0.5,
        maximum_required_dec_rate_deg_per_sec=0.3,
        requires_meridian_flip=False,
        meridian_flip_time_utc=None,
        rate_profile_id="simulator-default",
    )

    assert plan.start_time_utc == datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )


def test_rate_limit_warning_calculates_shortage() -> None:
    warning = RateLimitWarning(
        axis=Axis.RA,
        required_rate_deg_per_sec=1.5,
        available_rate_deg_per_sec=1.0,
    )

    assert warning.shortage_deg_per_sec == pytest.approx(0.5)


def test_ready_plan_rejects_rate_limit_warning() -> None:
    warning = RateLimitWarning(
        axis=Axis.RA,
        required_rate_deg_per_sec=1.5,
        available_rate_deg_per_sec=1.0,
    )

    with pytest.raises(ValueError):
        create_plan(
            status=TrackingPlanStatus.READY,
            rate_limit_warnings=(warning,),
        )


def test_degraded_plan_accepts_rate_limit_warning() -> None:
    warning = RateLimitWarning(
        axis=Axis.DEC,
        required_rate_deg_per_sec=1.5,
        available_rate_deg_per_sec=1.0,
    )

    plan = create_plan(
        status=TrackingPlanStatus.DEGRADED,
        rate_limit_warnings=(warning,),
    )

    assert plan.status is TrackingPlanStatus.DEGRADED
    assert plan.rate_limit_warnings == (warning,)


def test_blocked_plan_requires_reason() -> None:
    with pytest.raises(ValueError):
        create_plan(
            status=TrackingPlanStatus.BLOCKED,
        )


def test_meridian_flip_requires_planned_time() -> None:
    with pytest.raises(ValueError):
        create_plan(
            requires_meridian_flip=True,
        )


def test_meridian_flip_accepts_time_during_session() -> None:
    flip_time = datetime(
        2026,
        8,
        18,
        12,
        2,
        tzinfo=timezone.utc,
    )

    plan = create_plan(
        requires_meridian_flip=True,
        meridian_flip_time_utc=flip_time,
    )

    assert plan.meridian_flip_time_utc == flip_time