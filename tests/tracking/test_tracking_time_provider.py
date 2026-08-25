from datetime import datetime, timedelta, timezone
import math

import pytest

from astronavigator.scene.time import Time
from astronavigator.tracking import (
    SimulationTimeProvider,
    SystemUtcTimeProvider,
    TrackingRunMode,
    TrackingTimeSnapshot,
)


def test_tracking_time_snapshot_normalizes_to_utc() -> None:
    japan_timezone = timezone(timedelta(hours=9))

    snapshot = TrackingTimeSnapshot(
        utc=datetime(
            2026,
            8,
            18,
            21,
            0,
            tzinfo=japan_timezone,
        ),
        mode=TrackingRunMode.REHEARSAL,
        rate=1.0,
        is_paused=False,
    )

    assert snapshot.utc == datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )


def test_tracking_time_snapshot_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        TrackingTimeSnapshot(
            utc=datetime(2026, 8, 18, 12, 0),
            mode=TrackingRunMode.REHEARSAL,
            rate=1.0,
            is_paused=False,
        )


def test_tracking_time_snapshot_rejects_non_finite_rate() -> None:
    with pytest.raises(ValueError):
        TrackingTimeSnapshot(
            utc=datetime.now(timezone.utc),
            mode=TrackingRunMode.REHEARSAL,
            rate=math.inf,
            is_paused=False,
        )


def test_system_utc_time_provider_uses_current_utc() -> None:
    expected_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    provider = SystemUtcTimeProvider(
        now_function=lambda: expected_time,
    )

    snapshot = provider.get_snapshot()

    assert snapshot.utc == expected_time
    assert snapshot.mode is TrackingRunMode.OBSERVATION
    assert snapshot.rate == 1.0
    assert not snapshot.is_paused
    assert not snapshot.is_reverse
    assert not snapshot.is_stopped


def test_simulation_time_provider_reads_scene_time() -> None:
    time_model = Time(
        utc=datetime(
            2026,
            8,
            18,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        speed=-2.0,
        is_paused=False,
    )

    provider = SimulationTimeProvider(
        time_model_getter=lambda: time_model,
    )

    snapshot = provider.get_snapshot()

    assert snapshot.utc == time_model.utc
    assert snapshot.mode is TrackingRunMode.REHEARSAL
    assert snapshot.rate == -2.0
    assert snapshot.is_reverse
    assert not snapshot.is_stopped


def test_simulation_time_provider_reads_pause_state() -> None:
    time_model = Time(
        utc=datetime.now(timezone.utc),
        speed=1.0,
        is_paused=True,
    )

    provider = SimulationTimeProvider(
        time_model_getter=lambda: time_model,
    )

    snapshot = provider.get_snapshot()

    assert snapshot.is_paused
    assert snapshot.is_stopped


def test_simulation_provider_reads_replaced_time_model() -> None:
    current_time = Time(
        utc=datetime(
            2026,
            8,
            18,
            12,
            0,
            tzinfo=timezone.utc,
        )
    )

    provider = SimulationTimeProvider(
        time_model_getter=lambda: current_time,
    )

    first_snapshot = provider.get_snapshot()

    current_time = Time(
        utc=datetime(
            2026,
            8,
            19,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        speed=10.0,
    )

    second_snapshot = provider.get_snapshot()

    assert first_snapshot.utc != second_snapshot.utc
    assert second_snapshot.utc == current_time.utc
    assert second_snapshot.rate == 10.0


def test_get_time_returns_snapshot_utc() -> None:
    expected_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    provider = SystemUtcTimeProvider(
        now_function=lambda: expected_time,
    )

    assert provider.get_time() == expected_time