from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from astronavigator.sky.position import Position



class MountState(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    ERROR = "Error"


@dataclass(slots=True)
class Mount:
    state: MountState = MountState.DISCONNECTED
    driver_name: str | None = None
    position: Position | None = None

