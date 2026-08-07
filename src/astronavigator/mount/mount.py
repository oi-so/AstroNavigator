from __future__ import annotations

from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from serial.tools import list_ports


from astronavigator.sky.position import Position


@dataclass(slots=True)
class MountDevice:
    driver: type[Mount]
    name: str
    identifier: str
    description: str | None = None



class ConnectionState(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    ERROR = "Error"

class Axis(Enum):
    RA = "RA"
    DEC = "DEC"


class Mount(ABC):
    @property
    @abstractmethod
    def state(self) -> ConnectionState:
        ...

    @abstractmethod
    def update_status(self) -> None:
        ...

    @property
    @abstractmethod
    def position(self) -> Position:
        ...

    @property
    @abstractmethod
    def driver_name(self) -> str | None:
        ...

    @property
    @abstractmethod
    def is_tracking(self) -> bool:
        ...

    @property
    def is_connected(self) -> bool:
        return self.state == ConnectionState.CONNECTED

    @property
    @abstractmethod
    def is_slewing(self) -> bool:
        ...

    @abstractmethod
    def set_tracking(self, tracking: bool) -> None:
        ...


    @abstractmethod
    def connect(self) -> None:
        ...


    @abstractmethod
    def disconnect(self) -> None:
        ...


    @abstractmethod
    def move_axis(self, axis: Axis, speed: float) -> None:
        ...

    @abstractmethod
    def stop_axis(self, axis: Axis) -> None:
        ...


    @abstractmethod
    def slew_to(self, position: Position) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


    @abstractmethod
    def sync(self, position: Position) -> None:
        ...


    @classmethod
    @abstractmethod
    def discover(cls) -> list[MountDevice]:
        ...


    @classmethod
    @abstractmethod
    def create(cls, identifier: str) -> Mount:
        ...


    @staticmethod
    def find_ports() -> list[str]:
        ports = list_ports.comports()
        return [port.device for port in ports]



    @classmethod
    def discover_all(cls) -> list[MountDevice]:
        all_devices: list[MountDevice] = []
        for subclass in cls.__subclasses__():
            try:
                devices = subclass.discover()
                all_devices.extend(devices)
            except Exception as e:
                print(f"Error discovering devices for {subclass.__name__}: {e}")
        return all_devices