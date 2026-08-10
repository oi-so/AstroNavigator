from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo



@dataclass(slots=True)
class Time:
    utc: datetime
    speed: float = 1.0
    is_paused: bool = False

    def __post_init__(self) -> None:
        if self.utc.tzinfo is None:
            raise ValueError("utc must be timezone-aware")
        self.utc = self.utc.astimezone(timezone.utc)

    @classmethod
    def now(cls) -> "Time":
        return cls(utc=datetime.now(timezone.utc))


    def to_local_time(self, timezone: ZoneInfo) -> datetime:
        return self.utc.astimezone(timezone)


    def get_date_string(self, zone_info: ZoneInfo) -> str:
        local_time = self.to_local_time(zone_info)
        return local_time.strftime("%Y-%m-%d")

    def get_time_string(self, zone_info: ZoneInfo) -> str:
        local_time = self.to_local_time(zone_info)
        return local_time.strftime("%H:%M:%S")

    def get_datetime_string(self, zone_info: ZoneInfo) -> str:
        local_time = self.to_local_time(zone_info)
        return local_time.strftime("%Y-%m-%d %H:%M:%S %Z")


    def advance(self, seconds: float) -> None:
        if self.is_paused:
            return

        self.utc += timedelta(seconds=seconds * self.speed)


    def set_speed(self, speed: float) -> None:
        self.speed = speed

    def set_paused(self, paused: bool) -> None:
        self.is_paused = paused

    def reset_to_now(self) -> None:
        self.utc = datetime.now(timezone.utc)
        self.speed = 1.0
        self.is_paused = False