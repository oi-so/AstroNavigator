from __future__ import annotations

from enum import Enum
from abc import ABC, abstractmethod

from astronavigator.sky.position import Position



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
    @abstractmethod
    def is_connected(self) -> bool:
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

    

