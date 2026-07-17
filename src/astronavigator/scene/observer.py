from dataclasses import dataclass
from zoneinfo import ZoneInfo

@dataclass(slots=True)
class Observer:
    latitude: float
    longitude: float
    elevation: float
    timezone: ZoneInfo