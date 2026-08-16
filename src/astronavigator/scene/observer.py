from dataclasses import dataclass
from zoneinfo import ZoneInfo

@dataclass(slots=True)
class Observer:
    latitude: float
    longitude: float
    elevation: float
    timezone: ZoneInfo

    @classmethod
    def default(cls) -> "Observer":
        return cls(
            latitude=35.6924721,
            longitude=139.4128306,
            elevation=100.0,
            timezone=ZoneInfo("Asia/Tokyo"),
        )