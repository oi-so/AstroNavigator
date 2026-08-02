from __future__ import annotations

from PySide6.QtCore import QPointF
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import SkyObject


class ObjectIndex:
    def __init__(self) -> None:
        self._objects: list[SkyObject] = []

        self._id_index: dict[str, SkyObject] = {}
        self._hip_index: dict[int, SkyObject] = {}
        self._name_index: dict[str, SkyObject] = {}
        self._type_index: dict[ObjectType, list[SkyObject]] = {}

    def update(self, objects: list[SkyObject]):
        self._objects = list(objects)
        self._id_index.clear()
        self._hip_index.clear()
        self._name_index.clear()
        self._type_index.clear()

        for obj in self._objects:
            self._id_index[obj.id] = obj
            if obj.hip is not None:
                self._hip_index[obj.hip] = obj

            if obj.name:
                self._name_index[obj.name] = obj

            self._type_index.setdefault(obj.object_type, []).append(obj)

    def find_by_id(self, id: str) -> SkyObject | None:
        return self._id_index.get(id)

    def find_by_name(self, name: str) -> SkyObject | None:
        return self._name_index.get(name)

    def find_by_type(self, object_type: ObjectType) -> list[SkyObject]:
        return self._type_index.get(object_type, [])

    def find_by_hip(self, hip: int) -> SkyObject | None:
        return self._hip_index.get(hip)

    # TODO: Implement find_nearest()
    def find_nearest(self, position: QPointF, max_distance: float) -> SkyObject | None:
        pass