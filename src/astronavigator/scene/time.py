from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Time:
    utc: datetime
    speed: float = 1.0
    is_paused: bool = False