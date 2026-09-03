from __future__ import annotations

from dataclasses import dataclass
import math
import time

from astronavigator.mount.mount import Axis, ConnectionState, Mount, MountDevice
from astronavigator.mount.slew_path import PierSide
from astronavigator.mount.synscan.synscan_app_client import DEFAULT_SYN_SCAN_APP_HOST, DEFAULT_SYN_SCAN_APP_PORT, SynScanAppClient, SynScanAppConnectionError
from astronavigator.sky.position import Position


DEFAULT_MOUNT_CONNECTION_TIMEOUT_SEC = 15.0
MOUNT_CONNECTION_POLL_INTERVAL_SEC = 0.25

ASCOM_PRIMARY_AXIS = 0
ASCOM_SECONDARY_AXIS = 1

ASCOM_PIER_EAST = 0
ASCOM_PIER_WEST = 1
ASCOM_PIER_UNKNOWN = -1


@dataclass(frozen=True, slots=True)
class SynScanMountSettings:
    host: str = DEFAULT_SYN_SCAN_APP_HOST
    port: int = DEFAULT_SYN_SCAN_APP_PORT
    command_timeout_sec: float = 2.0
    mount_connection_timeout_sec: float = DEFAULT_MOUNT_CONNECTION_TIMEOUT_SEC

    def __post_init__(self) -> None:
        if not self.host:
            raise ValueError("host must not be empty.")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535.")

        timeout_values = {
            "command_timeout_sec": self.command_timeout_sec,
            "mount_connection_timeout_sec": self.mount_connection_timeout_sec,
        }
        for name, value in timeout_values.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be a positive finite number.")


class SynScanMount(Mount):
    def __init__(
        self,
        settings: SynScanMountSettings | None = None,
        *,
        client: SynScanAppClient | None = None,
    ) -> None:
        self._settings = settings or SynScanMountSettings()
        self._client = client or SynScanAppClient(
            host=self._settings.host,
            port=self._settings.port,
            timeout_sec=self._settings.command_timeout_sec,
        )

        self._state = ConnectionState.DISCONNECTED
        self._driver_name: str | None = None
        self._position: Position | None = None
        self._is_tracking = False
        self._is_slewing = False
        self._axis_rates_deg_per_sec = {
            Axis.RA: 0.0,
            Axis.DEC: 0.0,
        }
        self._pier_side = PierSide.UNKNOWN
        self._connected_by_this_mount = False

        self._can_sync = False
        self._can_slew = False
        self._can_home = False
        self._can_move_axis = False
        self._can_set_tracking = False
        self._can_set_pier_side = False

    @property
    def settings(self) -> SynScanMountSettings:
        return self._settings

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def driver_name(self) -> str | None:
        return self._driver_name

    @property
    def position(self) -> Position:
        self._require_connected()
        if self._position is None:
            self._position = self._get_position()
        return Position(self._position.ra_deg, self._position.dec_deg)

    @property
    def is_tracking(self) -> bool:
        return self._is_tracking

    @property
    def is_slewing(self) -> bool:
        return self._is_slewing

    @property
    def pier_side(self) -> PierSide:
        return self._pier_side

    @property
    def can_set_pier_side(self) -> bool:
        return False

    @property
    def can_sync(self) -> bool:
        return self._can_sync

    @property
    def can_slew(self) -> bool:
        return self._can_slew

    @property
    def can_home(self) -> bool:
        return self._can_home

    @property
    def can_move_axis(self) -> bool:
        return self._can_move_axis

    def connect(self) -> None:
        if self._state is ConnectionState.CONNECTED:
            return

        self._state = ConnectionState.CONNECTING
        self._connected_by_this_mount = False

        try:
            self._client.probe()
            app_version = self._get_single_action_value("AppVersionGet")
            self._driver_name = f"Sky-Watcher SynScan Pro {app_version}"

            mount_connection_state = self._get_mount_connection_state()
            if mount_connection_state == 0:
                self._client.action("ConnectedSet", 1)
                self._connected_by_this_mount = True

            self._wait_until_mount_connected()
            self._load_capabilities()
            self._state = ConnectionState.CONNECTED
            self.update_status()
        except Exception:
            self._state = ConnectionState.ERROR
            raise

    def disconnect(self) -> None:
        try:
            if self._connected_by_this_mount:
                self._client.action("ConnectedSet", 0)
        finally:
            self._connected_by_this_mount = False
            self._driver_name = None
            self._position = None
            self._is_tracking = False
            self._is_slewing = False
            self._axis_rates_deg_per_sec = {
                Axis.RA: 0.0,
                Axis.DEC: 0.0,
            }
            self._pier_side = PierSide.UNKNOWN
            self._state = ConnectionState.DISCONNECTED

    def update_status(self) -> None:
        self._require_connected()
        self._position = self._get_position()
        self._is_tracking = self._get_boolean("TrackingGet")
        self._is_slewing = self._get_boolean("SlewingGet")
        self._pier_side = self._get_pier_side()

    def set_tracking(self, tracking: bool) -> None:
        self._require_connected()
        if not self._can_set_tracking:
            raise NotImplementedError(
                "The connected SynScan mount cannot change tracking state."
            )

        self._client.command("TrackingSet", tracking)
        self._is_tracking = tracking

    def move_axis(self, axis: Axis, speed: float) -> None:
        """指定軸を度/秒で連続駆動する。0.0を指定すると停止する。"""

        self._require_connected()
        if not self._can_move_axis:
            raise NotImplementedError(
                "The connected SynScan mount does not support MoveAxis."
            )
        if not math.isfinite(speed):
            raise ValueError("rate_deg_per_sec must be finite.")

        self._client.command(
            "MoveAxis",
            self._axis_number(axis),
            speed,
        )
        self._axis_rates_deg_per_sec[axis] = speed
        self._is_slewing = any(
            not math.isclose(rate, 0.0, abs_tol=1e-12)
            for rate in self._axis_rates_deg_per_sec.values()
        )

    def stop_axis(self, axis: Axis) -> None:
        self.move_axis(axis, 0.0)

    def slew_to(
        self,
        position: Position,
        *,
        pier_side: PierSide | None = None,
    ) -> None:
        self._require_connected()
        if not self._can_slew:
            raise NotImplementedError(
                "The connected SynScan mount does not support equatorial slew."
            )
        if pier_side is not None and pier_side is not PierSide.UNKNOWN:
            raise NotImplementedError(
                "Selecting the destination pier side is not implemented for "
                "SynScanMount. SynScan Pro will select the pier side."
            )

        target = position.normalized()
        self._client.command(
            "SlewToCoordinatesAsync",
            target.ra_hours,
            target.dec_deg,
        )
        self._is_slewing = True

    def stop(self) -> None:
        self._require_connected()
        self._client.command("AbortSlew")
        self._axis_rates_deg_per_sec = {
            Axis.RA: 0.0,
            Axis.DEC: 0.0,
        }
        self._is_slewing = False

    def sync(
        self,
        position: Position,
        *,
        pier_side: PierSide | None = None,
    ) -> None:
        self._require_connected()
        if not self._can_sync:
            raise NotImplementedError(
                "The connected SynScan mount does not support equatorial sync."
            )

        target = position.normalized()
        self._client.command(
            "SyncToCoordinates",
            target.ra_hours,
            target.dec_deg,
        )
        self._position = target

    def home(self) -> None:
        self._require_connected()
        if not self._can_home:
            raise NotImplementedError(
                "The connected SynScan mount does not support finding home."
            )
        self._client.command("FindHome")

    def _load_capabilities(self) -> None:
        self._can_sync = self._get_boolean("CanSyncGet")
        self._can_slew = self._get_boolean("CanSlewAsyncGet")
        self._can_home = self._get_boolean("CanFindHomeGet")
        self._can_set_tracking = self._get_boolean("CanSetTrackingGet")
        self._can_set_pier_side = self._get_boolean("CanSetPierSideGet")
        self._can_move_axis = all(
            self._get_boolean("CanMoveAxis", axis_number)
            for axis_number in (ASCOM_PRIMARY_AXIS, ASCOM_SECONDARY_AXIS)
        )

    def _get_position(self) -> Position:
        values = self._client.command("RightAscensionDeclinationGet")
        if len(values) != 2:
            raise SynScanAppConnectionError(
                "RightAscensionDeclinationGet must return two values."
            )

        try:
            ra_hours, dec_deg = (float(value) for value in values)
        except ValueError as error:
            raise SynScanAppConnectionError(
                "SynScan Pro returned invalid equatorial coordinates."
            ) from error

        if not math.isfinite(ra_hours) or not math.isfinite(dec_deg):
            raise SynScanAppConnectionError(
                "SynScan Pro returned non-finite equatorial coordinates."
            )

        return Position(ra_hours * 15.0, dec_deg).normalized()

    def _get_pier_side(self) -> PierSide:
        values = self._client.command("SideOfPierGet")
        if len(values) != 1:
            raise SynScanAppConnectionError(
                "SideOfPierGet must return one value."
            )

        try:
            value = int(values[0])
        except ValueError as error:
            raise SynScanAppConnectionError(
                "SynScan Pro returned an invalid pier side."
            ) from error

        if value == ASCOM_PIER_EAST:
            return PierSide.EAST
        if value == ASCOM_PIER_WEST:
            return PierSide.WEST
        if value == ASCOM_PIER_UNKNOWN:
            return PierSide.UNKNOWN
        raise SynScanAppConnectionError(
            f"SynScan Pro returned an unknown pier side value: {value}."
        )

    def _get_boolean(
        self,
        command_name: str,
        *arguments: str | int | float | bool,
    ) -> bool:
        values = self._client.command(command_name, *arguments)
        if len(values) != 1 or values[0] not in ("0", "1"):
            raise SynScanAppConnectionError(
                f"{command_name} must return 0 or 1."
            )
        return values[0] == "1"

    def _get_single_action_value(self, action_name: str) -> str:
        values = self._client.action(action_name)
        if len(values) != 1:
            raise SynScanAppConnectionError(
                f"{action_name} must return one value."
            )
        return values[0]

    def _get_mount_connection_state(self) -> int:
        value = self._get_single_action_value("ConnectedGet")
        try:
            state = int(value)
        except ValueError as error:
            raise SynScanAppConnectionError(
                "ConnectedGet returned an invalid connection state."
            ) from error

        if state not in (0, 1, 2):
            raise SynScanAppConnectionError(
                f"ConnectedGet returned an unknown connection state: {state}."
            )
        return state

    def _wait_until_mount_connected(self) -> None:
        deadline = time.monotonic() + self._settings.mount_connection_timeout_sec

        while time.monotonic() < deadline:
            connection_state = self._get_mount_connection_state()
            if connection_state == 1:
                return
            if connection_state == 0 and self._connected_by_this_mount:
                raise SynScanAppConnectionError(
                    "SynScan Pro failed to connect to the mount. Check the "
                    "connection settings in SynScan Pro."
                )
            time.sleep(MOUNT_CONNECTION_POLL_INTERVAL_SEC)

        raise SynScanAppConnectionError(
            "Timed out while waiting for SynScan Pro to connect to the mount."
        )

    def _require_connected(self) -> None:
        if self._state is not ConnectionState.CONNECTED:
            raise RuntimeError("SynScan mount is not connected.")

    @staticmethod
    def _axis_number(axis: Axis) -> int:
        if axis is Axis.RA:
            return ASCOM_PRIMARY_AXIS
        if axis is Axis.DEC:
            return ASCOM_SECONDARY_AXIS
        raise ValueError(f"Unsupported axis: {axis}")

    @classmethod
    def discover(cls) -> list[MountDevice]:
        settings = SynScanMountSettings()
        client = SynScanAppClient(
            host=settings.host,
            port=settings.port,
            timeout_sec=settings.command_timeout_sec,
        )

        try:
            client.probe()
            app_version = client.action("AppVersionGet")
        except SynScanAppConnectionError:
            return []

        version_text = app_version[0] if len(app_version) == 1 else "unknown"
        identifier = f"{settings.host}:{settings.port}"
        return [
            MountDevice(
                driver=cls,
                name=f"SynScan Pro {version_text}",
                identifier=identifier,
                description="SynScan Pro経由で接続するSky-Watcher架台",
            )
        ]

    @classmethod
    def create(cls, identifier: str) -> Mount:
        host, separator, port_text = identifier.rpartition(":")
        if not separator or not host:
            raise ValueError(
                "SynScan identifier must have the form host:port."
            )

        try:
            port = int(port_text)
        except ValueError as error:
            raise ValueError(
                "SynScan identifier contains an invalid port."
            ) from error

        return cls(SynScanMountSettings(host=host, port=port))