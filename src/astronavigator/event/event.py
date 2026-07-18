from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from .event_type import EventType

@dataclass(slots=True)
class Event:
    event_type: EventType
    payload: Any | None = None