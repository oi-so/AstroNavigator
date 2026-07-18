from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from astronavigator.sky.object_tree import ObjectType
from astronavigator.sky.position import Position


@dataclass(slots=True)
class SkyObject(ABC):
    id: str
    name: str
    object_type: ObjectType
    
    @abstractmethod
    def get_position(self) -> Position:
        pass


class Star(SkyObject):
    def get_position(self) -> Position:
        return Position(0.0, 0.0)


class Moon(SkyObject):
    pass


class Satellite(SkyObject):
    pass


class Comet(SkyObject):
    pass


class DeepSkyObject(SkyObject):
    pass