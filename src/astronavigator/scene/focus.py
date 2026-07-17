from dataclasses import dataclass

from astronavigator.sky.sky_object import SkyObject


@dataclass(slots=True)
class Focus:
    target: SkyObject | None = None