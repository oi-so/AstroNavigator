from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.magnitude import Magnitude


@dataclass(slots=True)
class SkyObject(ABC):
    id: str
    name: str
    object_type: ObjectType

    @abstractmethod
    def get_position(self) -> Position:
        ...

    @abstractmethod
    def get_magnitude(self) -> Magnitude:
        ...


@dataclass(slots=True)
class Star(SkyObject):
    _position: Position
    _magnitude: Magnitude
    def get_position(self) -> Position:
        return self._position
    
    def get_magnitude(self) -> Magnitude:
        return self._magnitude

@dataclass(slots=True)
class Moon(SkyObject):
    def get_position(self) -> Position:
        raise NotImplementedError("Moon position calculation is not implemented yet.")

    def get_magnitude(self) -> Magnitude:
        raise NotImplementedError("Moon magnitude calculation is not implemented yet.")


@dataclass(slots=True)

class Satellite(SkyObject):
    def get_position(self) -> Position:
        raise NotImplementedError("Satellite position calculation is not implemented yet.")

    def get_magnitude(self) -> Magnitude:
        raise NotImplementedError("Satellite magnitude calculation is not implemented yet.")


@dataclass(slots=True)
class Comet(SkyObject):
    def get_position(self) -> Position:
        raise NotImplementedError("Comet position calculation is not implemented yet.")
    
    def get_magnitude(self) -> Magnitude:
        raise NotImplementedError("Comet magnitude calculation is not implemented yet.")


@dataclass(slots=True)
class DeepSkyObject(SkyObject):
    _position: Position
    _magnitude: Magnitude
    def get_position(self) -> Position:
        return self._position
    
    def get_magnitude(self) -> Magnitude:
        return self._magnitude