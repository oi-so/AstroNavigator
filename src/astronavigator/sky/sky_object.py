from __future__ import annotations

from dataclasses import dataclass

from astronavigator.sky.object_tree import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.magnitude import Magnitude


@dataclass(slots=True)
class SkyObject:
    id: str
    name: str
    object_type: ObjectType
    position: Position
    magnitude: Magnitude


class Star(SkyObject):
    pass


class Moon(SkyObject):
    pass


class Satellite(SkyObject):
    pass


class Comet(SkyObject):
    pass


class DeepSkyObject(SkyObject):
    pass