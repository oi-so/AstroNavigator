from __future__ import annotations

import bisect
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

        self._magnitude_sorted_objects: dict[ObjectType, list[SkyObject]] = {}
        self._magnitude_sorted_values: dict[ObjectType, list[float]] = {}

    def update(self, objects: list[SkyObject]):
        self._objects = list(objects)
        self._id_index.clear()
        self._hip_index.clear()
        self._name_index.clear()
        self._type_index.clear()
        self._magnitude_sorted_objects.clear()
        self._magnitude_sorted_values.clear()

        for obj in self._objects:
            self._id_index[obj.id] = obj
            if obj.hip is not None:
                self._hip_index[obj.hip] = obj

            if obj.name:
                self._name_index[obj.name] = obj

            self._type_index.setdefault(obj.object_type, []).append(obj)

        for object_type, objects_of_type in self._type_index.items():
            self._build_magnitude_index(object_type, objects_of_type)

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

    def _build_magnitude_index(self, object_type: ObjectType, objects_of_type: list[SkyObject]) -> None:
        try:
            pairs = [(obj.get_magnitude().value, obj) for obj in objects_of_type]
        except NotImplementedError:
            return

        pairs.sort(key=lambda x: x[0])
        self._magnitude_sorted_values[object_type] = [value for value, _ in pairs]
        self._magnitude_sorted_objects[object_type] = [obj for _, obj in pairs]

    def find_visible_by_type(self, object_type: ObjectType, limit_magnitude: float) -> list[SkyObject]:
        sorted_objects = self._magnitude_sorted_objects.get(object_type)
        if sorted_objects is None:
            return [obj for obj in self._type_index.get(object_type, []) if obj.get_magnitude().is_visible(limit_magnitude)]
        
        sorted_values = self._magnitude_sorted_values[object_type]
        index = bisect.bisect_right(sorted_values, limit_magnitude)
        return sorted_objects[:index]
