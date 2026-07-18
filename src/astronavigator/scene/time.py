from dataclasses import dataclass
from datetime import datetime, timezone




@dataclass(slots=True)
class Time:
    utc: datetime
    speed: float = 1.0
    is_paused: bool = False

    @classmethod
    def now(cls) -> "Time":
        return cls(utc=datetime.now(timezone.utc))