from __future__ import annotations

from collections.abc import Sequence
import math
import socket
from threading import Lock


DEFAULT_SYN_SCAN_APP_HOST = "127.0.0.1"
DEFAULT_SYN_SCAN_APP_PORT = 11881
DEFAULT_SYN_SCAN_APP_TIMEOUT_SEC = 2.0
MAXIMUM_DATAGRAM_SIZE = 65535


class SynScanAppError(RuntimeError):
    pass


class SynScanAppConnectionError(SynScanAppError):
    pass


class SynScanAppCommandError(SynScanAppError):
    def __init__(
        self,
        status: str,
        command_name: str,
        details: Sequence[str] = (),
    ) -> None:
        self.status = status
        self.command_name = command_name
        self.details = tuple(details)

        detail_text = ",".join(self.details)
        message = f"SynScan command failed: {status},{command_name}"
        if detail_text:
            message += f",{detail_text}"

        super().__init__(message)


class SynScanAppClient:
    """SynScan Pro の SynScan App Protocol をUDPで呼び出す。"""

    def __init__(
        self,
        host: str = DEFAULT_SYN_SCAN_APP_HOST,
        port: int = DEFAULT_SYN_SCAN_APP_PORT,
        timeout_sec: float = DEFAULT_SYN_SCAN_APP_TIMEOUT_SEC,
    ) -> None:
        if not host:
            raise ValueError("host must not be empty.")
        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535.")
        if not math.isfinite(timeout_sec) or timeout_sec <= 0.0:
            raise ValueError("timeout_sec must be a positive finite number.")

        self._host = host
        self._port = port
        self._timeout_sec = timeout_sec
        self._lock = Lock()

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    def probe(self) -> str:
        values = self.command("ServerVersion")
        if not values:
            raise SynScanAppConnectionError(
                "SynScan Pro returned an empty server version."
            )
        return ".".join(values)

    def command(
        self,
        command_name: str,
        *arguments: str | int | float | bool,
    ) -> tuple[str, ...]:
        if not command_name or not command_name.isalpha():
            raise ValueError(
                "command_name must contain alphabetic characters only."
            )

        command_text = ",".join(
            [command_name, *(self._format_argument(value) for value in arguments)]
        )
        response_text = self._exchange(command_text)
        response_parts = tuple(response_text.split(","))

        if len(response_parts) < 2:
            raise SynScanAppConnectionError(
                f"Invalid response from SynScan Pro: {response_text!r}"
            )

        status, response_command = response_parts[:2]
        values = response_parts[2:]

        if response_command.casefold() != command_name.casefold():
            raise SynScanAppConnectionError(
                "SynScan Pro returned a response for a different command: "
                f"expected {command_name!r}, received {response_command!r}."
            )

        if status != "Ok":
            raise SynScanAppCommandError(status, response_command, values)

        return values

    def action(
        self,
        action_name: str,
        *arguments: str | int | float | bool,
    ) -> tuple[str, ...]:
        values = self.command("Action", action_name, *arguments)
        if not values:
            raise SynScanAppConnectionError(
                f"SynScan Pro returned no action name for {action_name!r}."
            )

        response_action, *response_values = values
        if response_action.casefold() != action_name.casefold():
            raise SynScanAppConnectionError(
                "SynScan Pro returned a response for a different action: "
                f"expected {action_name!r}, received {response_action!r}."
            )

        return tuple(response_values)

    def _exchange(self, command_text: str) -> str:
        command_bytes = command_text.encode("ascii")

        with self._lock:
            try:
                address_info = socket.getaddrinfo(
                    self._host,
                    self._port,
                    family=socket.AF_INET,
                    type=socket.SOCK_DGRAM,
                )
                address = address_info[0][4]

                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                    udp_socket.settimeout(self._timeout_sec)
                    udp_socket.sendto(command_bytes, address)
                    response_bytes, _ = udp_socket.recvfrom(MAXIMUM_DATAGRAM_SIZE)
            except TimeoutError as error:
                raise SynScanAppConnectionError(
                    "SynScan Pro did not respond. Check that SynScan Pro is "
                    f"running and its protocol server is available at "
                    f"{self._host}:{self._port}."
                ) from error
            except OSError as error:
                raise SynScanAppConnectionError(
                    "Failed to communicate with SynScan Pro at "
                    f"{self._host}:{self._port}: {error}"
                ) from error

        try:
            return response_bytes.decode("ascii").strip("\x00\r\n ")
        except UnicodeDecodeError as error:
            raise SynScanAppConnectionError(
                "SynScan Pro returned a non-ASCII response."
            ) from error

    @staticmethod
    def _format_argument(value: str | int | float | bool) -> str:
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("Floating-point arguments must be finite.")
            return format(value, ".15g")
        if isinstance(value, str):
            if "," in value:
                raise ValueError("String arguments must not contain commas.")
            return value
        raise TypeError(f"Unsupported SynScan argument type: {type(value)!r}")