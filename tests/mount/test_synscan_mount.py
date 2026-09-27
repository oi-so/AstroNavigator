from __future__ import annotations

import pytest

from astronavigator.mount.mount import Axis, ConnectionState
from astronavigator.mount.slew_path import PierSide
from astronavigator.mount.synscan.synscan_app_client import SynScanAppConnectionError
from astronavigator.mount.synscan.synscan_mount import SynScanMount, SynScanMountSettings
from astronavigator.sky.position import Position

from conftest import FakeSynScanAppClient


@pytest.fixture()
def connected_mount() -> tuple[SynScanMount, FakeSynScanAppClient]:
    client = FakeSynScanAppClient()
    mount = SynScanMount(SynScanMountSettings(), client=client)
    mount.connect()
    return mount, client


def test_is_synced_false_until_sync_succeeds(connected_mount) -> None:
    mount, _client = connected_mount

    assert mount.is_synced is False

    mount.sync(Position(150.0, 45.0))

    assert mount.is_synced is True


def test_sync_failure_keeps_is_synced_false_and_raises_clear_error(connected_mount) -> None:
    mount, client = connected_mount
    client.raise_on_sync = SynScanAppConnectionError("did not respond")

    with pytest.raises(SynScanAppConnectionError) as excinfo:
        mount.sync(Position(150.0, 45.0))

    assert mount.is_synced is False
    assert "確認ポップアップ" in str(excinfo.value)


def test_home_resets_sync_state(connected_mount) -> None:
    mount, _client = connected_mount

    mount.sync(Position(150.0, 45.0))
    assert mount.is_synced is True

    mount.home()

    assert mount.is_synced is False
    assert mount.pier_side is PierSide.UNKNOWN


def test_can_set_pier_side_reflects_ascom_capability_only(connected_mount) -> None:
    mount, client = connected_mount

    # CanSetPierSideGet が "0" のフィクスチャなので、SideOfPier の強制書き換えは不可。
    assert mount.can_set_pier_side is False
    # GoTo時に架台姿勢を明示指定する手段はSynScan App Protocolに存在しない。
    assert mount.supports_goto_pier_side is False


def test_slew_to_ignores_requested_pier_side_without_error(connected_mount) -> None:
    mount, client = connected_mount

    # SynScanでは pier_side を指定しても例外にならず、SynScan Proの自動判断に委ねる。
    mount.slew_to(Position(150.0, 45.0), pier_side=PierSide.EAST)

    slew_calls = [call for call in client.calls if call[0] == "SlewToCoordinatesAsync"]
    assert len(slew_calls) == 1


def test_disconnect_clears_is_synced(connected_mount) -> None:
    mount, _client = connected_mount

    mount.sync(Position(150.0, 45.0))
    assert mount.is_synced is True

    mount.disconnect()

    assert mount.is_synced is False


def test_move_axis_clamped_by_tracking_backend_not_mount(connected_mount) -> None:
    # SynScanMount.move_axis自体はクランプしない（呼び出し側の責務）ことを確認する。
    mount, client = connected_mount

    mount.move_axis(Axis.RA, 5.0)

    move_calls = [call for call in client.calls if call[0] == "MoveAxis"]
    assert move_calls[-1][1] == (0, 5.0)
