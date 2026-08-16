from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GeographicLocation:
    latitude: float
    longitude: float
    elevation: float | None


LocationCallback = Callable[[GeographicLocation], None]
LocationErrorCallback = Callable[[str], None]


class LocationProvider(Protocol):
    def request_location(self, on_location: LocationCallback, on_error: LocationErrorCallback) -> None: 
        ...