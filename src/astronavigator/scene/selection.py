from dataclasses import dataclass

from astronavigator.sky.sky_object import SkyObject


@dataclass(slots=True)
class Selection:
    selected: SkyObject | None = None   