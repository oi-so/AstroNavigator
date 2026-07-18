from __future__ import annotations
from collections.abc import Callable
from collections import defaultdict
from typing import Any


from .event import Event
from .event_type import EventType


class EventBus:
    def __init__(self):
        self._subscribers: dict[EventType, list[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    def publish(self, event_type: EventType, payload: Any | None = None) -> None:
        if event_type in self._subscribers:
            event = Event(event_type, payload)

            for callback in self._subscribers[event_type]:
                callback(event)