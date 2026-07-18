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
            latitude=35.681236,
            longitude=139.767125,
            elevation=0.0,
            timezone=ZoneInfo("Asia/Tokyo"),
        )