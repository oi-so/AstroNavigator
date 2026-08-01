from __future__ import annotations

from dataclasses import dataclass, field

from astronavigator.sky.constellation_line import Constellation
from astronavigator.sky.sky_object import SkyObject



@dataclass(slots=True)
class Catalog:
    name: str
    objects: list[SkyObject] = field(default_factory=list)


@dataclass(slots=True)
class ConstellationCatalog:
    name: str
    constellations: list[Constellation] = field(default_factory=list)