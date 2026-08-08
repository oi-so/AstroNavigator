from __future__ import annotations

import bisect
import math
from PySide6.QtCore import QPointF

from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import SkyObject
from astronavigator.sky.position import Position


DEC_BIN_SIZE_DEC = 2.0
DEC_BIN_COUNT = math.ceil(180.0 / DEC_BIN_SIZE_DEC)


class ObjectIndex:
    def __init__(self) -> None:
        self._objects: list[SkyObject] = []

        self._id_index: dict[str, SkyObject] = {}
        self._hip_index: dict[int, SkyObject] = {}
        self._name_index: dict[str, SkyObject] = {}
        self._type_index: dict[ObjectType, list[SkyObject]] = {}

        # ObjectTypeをbin_indexごとに分けて、この中で等級で並び替え
        self._dec_bin_magnitudes: dict[ObjectType, list[list[float]]] = {}
        self._dec_bin_ra: dict[ObjectType, list[list[float]]] = {}
        self._dec_bin_objects: dict[ObjectType, list[list[SkyObject]]] = {}

    def update(self, objects: list[SkyObject]):
        self._objects = list(objects)
        self._id_index.clear()
        self._hip_index.clear()
        self._name_index.clear()
        self._type_index.clear()
        self._dec_bin_magnitudes.clear()
        self._dec_bin_ra.clear()
        self._dec_bin_objects.clear()

        for obj in self._objects:
            self._id_index[obj.id] = obj
            if obj.hip is not None:
                self._hip_index[obj.hip] = obj

            if obj.name:
                self._name_index[obj.name] = obj

            self._type_index.setdefault(obj.object_type, []).append(obj)

        for object_type, objects_of_type in self._type_index.items():
            self._build_spatial_magnitude_index(object_type, objects_of_type)

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

    def _build_spatial_magnitude_index(self, object_type: ObjectType, objects_of_type: list[SkyObject]) -> None:
        try:
            entries = [(obj.get_position().dec_deg, obj.get_magnitude().value, obj.get_position().ra_deg, obj) for obj in objects_of_type]
        except NotImplementedError:
            return

        bin_magnitudes: list[list[float]] = [[] for _ in range(DEC_BIN_COUNT)]
        bin_ra: list[list[float]] = [[] for _ in range(DEC_BIN_COUNT)]
        bin_objects: list[list[SkyObject]] = [[] for _ in range(DEC_BIN_COUNT)]

        for dec_deg, magnitude, ra_deg, obj in entries:
            bin_index = self._dec_to_bin_index(dec_deg)
            bin_magnitudes[bin_index].append(magnitude)
            bin_ra[bin_index].append(ra_deg)
            bin_objects[bin_index].append(obj)

        for bin_index in range(DEC_BIN_COUNT):
            if not bin_magnitudes[bin_index]:
                continue
            order = sorted(range(len(bin_magnitudes[bin_index])), key=lambda i: bin_magnitudes[bin_index][i])
            bin_magnitudes[bin_index] = [bin_magnitudes[bin_index][i] for i in order]
            bin_ra[bin_index] = [bin_ra[bin_index][i] for i in order]
            bin_objects[bin_index] = [bin_objects[bin_index][i] for i in order]

            self._dec_bin_magnitudes[object_type] = bin_magnitudes
            self._dec_bin_ra[object_type] = bin_ra
            self._dec_bin_objects[object_type] = bin_objects

    @staticmethod
    def _dec_to_bin_index(dec_deg: float) -> int:
        clamped = max(-90.0, min(90.0, dec_deg))
        index = int((clamped + 90.0) // DEC_BIN_SIZE_DEC)
        return min(max(0, index), DEC_BIN_COUNT - 1)

    def find_visible_by_type(self, object_type: ObjectType, limit_magnitude: float, min_position: Position | None = None, max_position: Position | None = None) -> list[SkyObject]:
        bin_magnitudes = self._dec_bin_magnitudes.get(object_type)
        if bin_magnitudes is None or min_position is None or max_position is None:
            return [obj for obj in self._type_index.get(object_type, []) if obj.get_magnitude().is_visible(limit_magnitude)]
        bin_ra = self._dec_bin_ra.get(object_type)
        bin_objects = self._dec_bin_objects.get(object_type)
        start_bin = self._dec_to_bin_index(min_position.dec_deg)
        end_bin = self._dec_to_bin_index(max_position.dec_deg)

        min_ra = min_position.ra_deg
        max_ra = max_position.ra_deg
        wraps = min_ra > max_ra

        result: list[SkyObject] = []
        for bin_index in range(start_bin, end_bin + 1):
            mag_list = bin_magnitudes[bin_index]
            if not mag_list:
                continue

            count = bisect.bisect_right(mag_list, limit_magnitude)
            if count == 0:
                continue

            ra_list = bin_ra[bin_index]
            obj_list = bin_objects[bin_index]

            for i in range(count):
                ra_deg = ra_list[i]
                if wraps:
                    if ra_deg < min_ra and ra_deg > max_ra:
                        continue
                elif ra_deg < min_ra or ra_deg > max_ra:
                    continue
                result.append(obj_list[i])

        return result