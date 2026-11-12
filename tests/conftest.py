from __future__ import annotations


class FakeSynScanAppClient:
    """SynScanAppClientの最小スタブ。テストごとに応答をあらかじめ登録する。

    tests/mount と tests/tracking の両方から使うため、tests直下の
    conftest.py に置いている（testsはパッケージ化されていないため、
    tests.xxx としての絶対importはできない）。
    """

    def __init__(self) -> None:
        self.action_responses: dict[str, tuple[str, ...]] = {
            "AppVersionGet": ("2,0,0",),
            "ConnectedGet": ("1",),
        }
        self.command_responses: dict[str, tuple[str, ...]] = {
            "RightAscensionDeclinationGet": ("10.0", "20.0"),
            "TrackingGet": ("1",),
            "SlewingGet": ("0",),
            "SideOfPierGet": ("0",),
            "CanSyncGet": ("1",),
            "CanSlewAsyncGet": ("1",),
            "CanFindHomeGet": ("1",),
            "CanSetTrackingGet": ("1",),
            "CanSetPierSideGet": ("0",),
        }
        self.move_axis_capable = True
        self.calls: list[tuple[str, tuple]] = []
        self.raise_on_sync: Exception | None = None

    def probe(self) -> str:
        return "2.0.0"

    def action(self, action_name: str, *arguments) -> tuple[str, ...]:
        self.calls.append((f"action:{action_name}", arguments))
        return self.action_responses[action_name]

    def command(self, command_name: str, *arguments) -> tuple[str, ...]:
        self.calls.append((command_name, arguments))

        if command_name == "SyncToCoordinates" and self.raise_on_sync is not None:
            raise self.raise_on_sync

        if command_name == "CanMoveAxis":
            return ("1",) if self.move_axis_capable else ("0",)

        if command_name in ("FindHome", "MoveAxis", "AbortSlew", "SlewToCoordinatesAsync", "TrackingSet", "SyncToCoordinates"):
            return ("Ok", command_name)

        return self.command_responses[command_name]
