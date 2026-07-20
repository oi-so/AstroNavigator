from __future__ import annotations

from dataclasses import dataclass, field

from astronavigator.sky.sky_object import SkyObject



@dataclass(slots=True)
class Catalog:
    objects: list[SkyObject] = field(default_factory=list)