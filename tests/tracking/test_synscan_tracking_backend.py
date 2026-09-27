from __future__ import annotations

import pytest

from astronavigator.mount.synscan.synscan_mount import SynScanMount, SynScanMountSettings
from astronavigator.sky.position import Position
from astronavigator.tracking.synscan_tracking_backend import SynScanTrackingBackend
from conftest import FakeSynScanAppClient


@pytest.fixture()
def connected_synced_mount() -> tuple[SynScanMount, FakeSynScanAppClient]:
    client = FakeSynScanAppClient()
    mount = SynScanMount(
        SynScanMountSettings(
            maximum_ra_rate_deg_per_sec=1.5,
            maximum_dec_rate_deg_per_sec=1.5,
        ),
        client=client,
    )
    mount.connect()
    mount.sync(Position(150.0, 45.0))
    return mount, client


def test_start_requires_sync(connected_synced_mount) -> None:
    client = FakeSynScanAppClient()
    mount = SynScanMount(SynScanMountSettings(), client=client)
    mount.connect()

    backend = SynScanTrackingBackend(mount)

    with pytest.raises(RuntimeError):
        backend.start()


def test_start_succeeds_when_synced(connected_synced_mount) -> None:
    mount, _client = connected_synced_mount
    backend = SynScanTrackingBackend(mount)

    backend.start()

    assert backend.is_active is True


def test_apply_rates_clamps_to_maximum(connected_synced_mount) -> None:
    mount, client = connected_synced_mount
    backend = SynScanTrackingBackend(mount)
    backend.start()

    command = backend.apply_rates(10.0, -10.0)

    assert command.applied_ra_rate_deg_per_sec == pytest.approx(1.5)
    assert command.applied_dec_rate_deg_per_sec == pytest.approx(-1.5)
    assert command.ra_rate_limited is True
    assert command.dec_rate_limited is True

    move_calls = [call for call in client.calls if call[0] == "MoveAxis"]
    assert move_calls[-2][1] == (0, 1.5)
    assert move_calls[-1][1] == (1, -1.5)


def test_apply_rates_within_limit_is_not_flagged(connected_synced_mount) -> None:
    mount, _client = connected_synced_mount
    backend = SynScanTrackingBackend(mount)
    backend.start()

    command = backend.apply_rates(0.5, -0.5)

    assert command.applied_ra_rate_deg_per_sec == pytest.approx(0.5)
    assert command.ra_rate_limited is False
    assert command.dec_rate_limited is False


def test_stop_zeroes_axes(connected_synced_mount) -> None:
    mount, client = connected_synced_mount
    backend = SynScanTrackingBackend(mount)
    backend.start()
    backend.apply_rates(1.0, 1.0)

    backend.stop()

    assert backend.is_active is False
    move_calls = [call for call in client.calls if call[0] == "MoveAxis"]
    assert move_calls[-2][1] == (0, 0.0)
    assert move_calls[-1][1] == (1, 0.0)
