from __future__ import annotations

from datetime import datetime, timezone

from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.position import Position
from astronavigator.tracking.tracking_plan import TrackingPlan
from astronavigator.tracking.tracking_safety_policy import (
    TrackingSafetyContext,
    TrackingSafetyIssueCode,
    TrackingSafetyPolicy,
)
from astronavigator.tracking.tracking_state import (
    TrackingPlanStatus,
    TrackingRunMode,
)


def create_plan(
    *,
    status: TrackingPlanStatus = TrackingPlanStatus.READY,
    ra_rate: float = 1.0,
    dec_rate: float = 1.0,
    blocked_reason: str | None = None,
) -> TrackingPlan:
    start_time = datetime(
        2026,
        8,
        19,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return TrackingPlan(
        target_id="test:target",
        status=status,
        start_time_utc=start_time,
        end_time_utc=None,
        initial_pier_side=PierSide.UNKNOWN,
        preposition=Position(
            ra_deg=120.0,
            dec_deg=30.0,
        ),
        maximum_required_ra_rate_deg_per_sec=ra_rate,
        maximum_required_dec_rate_deg_per_sec=dec_rate,
        requires_meridian_flip=False,
        meridian_flip_time_utc=None,
        rate_profile_id="test-profile",
        blocked_reason=blocked_reason,
    )


def create_context(
    **changes: object,
) -> TrackingSafetyContext:
    values: dict[str, object] = {
        "run_mode": TrackingRunMode.OBSERVATION,
        "is_real_mount": True,
        "mount_connected": True,
        "mount_synchronized": True,
        "communication_healthy": True,
        "time_rate": 1.0,
        "available_ra_rate_deg_per_sec": 2.0,
        "available_dec_rate_deg_per_sec": 2.0,
    }
    values.update(changes)

    return TrackingSafetyContext(**values)  # type: ignore[arg-type]


def issue_codes(
    result_issues: tuple,
) -> set[TrackingSafetyIssueCode]:
    return {issue.code for issue in result_issues}


def test_safe_plan_can_start() -> None:
    result = TrackingSafetyPolicy().evaluate_before_start(
        create_plan(),
        create_context(),
    )

    assert result.status is TrackingPlanStatus.READY
    assert result.can_start
    assert not result.should_stop
    assert result.issues == ()


def test_disconnected_mount_blocks_start() -> None:
    result = TrackingSafetyPolicy().evaluate_before_start(
        create_plan(),
        create_context(mount_connected=False),
    )

    assert result.status is TrackingPlanStatus.BLOCKED
    assert not result.can_start
    assert (
        TrackingSafetyIssueCode.MOUNT_DISCONNECTED
        in issue_codes(result.issues)
    )


def test_rate_shortage_degrades_but_does_not_block() -> None:
    result = TrackingSafetyPolicy().evaluate_before_start(
        create_plan(
            ra_rate=5.0,
            dec_rate=3.0,
        ),
        create_context(
            available_ra_rate_deg_per_sec=2.0,
            available_dec_rate_deg_per_sec=2.0,
        ),
    )

    assert result.status is TrackingPlanStatus.DEGRADED
    assert result.can_start
    assert not result.should_stop
    assert (
        TrackingSafetyIssueCode.RA_RATE_LIMIT
        in issue_codes(result.issues)
    )
    assert (
        TrackingSafetyIssueCode.DEC_RATE_LIMIT
        in issue_codes(result.issues)
    )


def test_rate_shortage_does_not_stop_tracking() -> None:
    result = TrackingSafetyPolicy().evaluate_during_tracking(
        create_plan(ra_rate=5.0),
        create_context(
            available_ra_rate_deg_per_sec=2.0,
        ),
    )

    assert result.status is TrackingPlanStatus.DEGRADED
    assert not result.should_stop


def test_real_mount_cannot_use_fast_simulation() -> None:
    result = TrackingSafetyPolicy().evaluate_before_start(
        create_plan(),
        create_context(
            run_mode=TrackingRunMode.REHEARSAL,
            is_real_mount=True,
            time_rate=10.0,
        ),
    )

    assert result.status is TrackingPlanStatus.BLOCKED
    assert not result.can_start
    assert (
        TrackingSafetyIssueCode.INVALID_TIME_RATE
        in issue_codes(result.issues)
    )


def test_simulator_can_use_fast_rehearsal() -> None:
    result = TrackingSafetyPolicy().evaluate_before_start(
        create_plan(),
        create_context(
            run_mode=TrackingRunMode.REHEARSAL,
            is_real_mount=False,
            time_rate=10.0,
        ),
    )

    assert result.status is TrackingPlanStatus.READY
    assert result.can_start


def test_real_mount_time_jump_is_blocked() -> None:
    result = TrackingSafetyPolicy().evaluate_before_start(
        create_plan(),
        create_context(time_jump_requested=True),
    )

    assert result.status is TrackingPlanStatus.BLOCKED
    assert (
        TrackingSafetyIssueCode.REAL_MOUNT_TIME_JUMP
        in issue_codes(result.issues)
    )


def test_communication_error_stops_tracking() -> None:
    result = TrackingSafetyPolicy().evaluate_during_tracking(
        create_plan(),
        create_context(communication_healthy=False),
    )

    assert result.status is TrackingPlanStatus.BLOCKED
    assert result.should_stop
    assert (
        TrackingSafetyIssueCode.COMMUNICATION_ERROR
        in issue_codes(result.issues)
    )


def test_tracking_stops_below_minimum_altitude() -> None:
    result = TrackingSafetyPolicy().evaluate_during_tracking(
        create_plan(),
        create_context(
            current_altitude_deg=9.0,
            minimum_altitude_deg=10.0,
        ),
    )

    assert result.should_stop
    assert (
        TrackingSafetyIssueCode.BELOW_MINIMUM_ALTITUDE
        in issue_codes(result.issues)
    )


def test_blocked_plan_cannot_start() -> None:
    result = TrackingSafetyPolicy().evaluate_before_start(
        create_plan(
            status=TrackingPlanStatus.BLOCKED,
            blocked_reason="対象天体が昇りません。",
        ),
        create_context(),
    )

    assert result.status is TrackingPlanStatus.BLOCKED
    assert not result.can_start
    assert (
        TrackingSafetyIssueCode.PLAN_BLOCKED
        in issue_codes(result.issues)
    )