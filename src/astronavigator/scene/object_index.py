from __future__ import annotations

from PySide6.QtCore import QPointF
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import SkyObject


class ObjectIndex:
    def __init__(self) -> None:
        self._objects: list[SkyObject] = []

    def update(self, objects: list[SkyObject]):
        self._objects = list(objects)
    
    def find_by_id(self, object_id: str) -> SkyObject | None:
        for obj in self._objects:
            if obj.id == object_id:
                return obj
        return None

    def find_by_name(self, name: str) -> SkyObject | None:
        for obj in self._objects:
            if obj.name == name:
                return obj
        return None

    def find_by_type(self, object_type: ObjectType) -> list[SkyObject]:
        return [
            obj
            for obj in self._objects
            if obj.object_type == object_type
        ]

    # TODO: Implement find_nearest()
    def find_nearest(self, position: QPointF, max_distance: float) -> SkyObject | None:
        pass