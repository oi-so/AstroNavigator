from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo



@dataclass(slots=True)
class Time:
    utc: datetime
    speed: float = 1.0
    is_paused: bool = False

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