from __future__ import annotations

import math
from copy import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from astronavigator.scene.time import Time
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Satellite, SkyObject

if TYPE_CHECKING:
    from astronavigator.scene.observer import Observer
    from astronavigator.scene.scene import Scene


@dataclass(frozen=True, slots=True)
class DynamicRenderState:
    position: Position
    magnitude: Magnitude


@dataclass(slots=True)
class _PositionInterval:
    source: SkyObject
    model: SkyObject
    key: tuple[object, ...]
    start: datetime
    end: datetime
    first: DynamicRenderState
    last: DynamicRenderState


def interpolate_position(first: Position, last: Position, fraction: float) -> Position:
    # 赤経の0/360度境界と極付近でも、天球上の短い経路を通る。
    def vector(position: Position) -> tuple[float, float, float]:
        ra, dec = math.radians(position.ra_deg), math.radians(position.dec_deg)
        return math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)

    first_vector, last_vector = vector(first), vector(last)
    x, y, z = (
        a + (b - a) * fraction for a, b in zip(first_vector, last_vector, strict=True)
    )
    return Position(
        math.degrees(math.atan2(y, x)) % 360,
        math.degrees(math.atan2(z, math.hypot(x, y))),
    ).normalized()


class DynamicRenderCache:
    def __init__(self) -> None:
        self._intervals: dict[str, _PositionInterval] = {}

    def calculate(self, scene: Scene) -> dict[str, DynamicRenderState]:
        candidates: dict[str, SkyObject] = {}
        for target in (scene.selection.selected, scene.focus.target):
            if target is not None and target.is_dynamic:
                candidates[target.id] = target
        for object_type in (ObjectType.SUN, ObjectType.MOON, ObjectType.PLANET):
            for obj in scene.object_index.find_dynamic_by_type(object_type):
                candidates[obj.id] = obj
        for snapshot, limit in (
            (
                scene.comet_render_snapshot,
                scene.rendering_settings.comet_limiting_magnitude,
            ),
            (
                scene.satellite_render_snapshot,
                scene.rendering_settings.satellite_limiting_magnitude,
            ),
        ):
            if snapshot is None:
                continue
            for object_id, state in snapshot.states.items():
                magnitude = (
                    state.magnitude
                    if hasattr(state, "magnitude")
                    else state.brightness.magnitude
                )
                if magnitude.is_visible(limit):
                    obj = scene.object_index.find_by_id(object_id)
                    if obj is not None:
                        candidates[obj.id] = obj
        states = {}
        for object_id, obj in candidates.items():
            try:
                states[object_id] = self._calculate_object(
                    obj, scene.time, scene.observer
                )
            except (ValueError, RuntimeError, ArithmeticError):
                # 暦の範囲外や無効な軌道では、別時刻の位置を流用しない。
                self._intervals.pop(object_id, None)
        self._intervals = {
            key: value for key, value in self._intervals.items() if key in candidates
        }
        return states

    def _calculate_object(
        self, obj: SkyObject, time: Time, observer: Observer
    ) -> DynamicRenderState:
        key = (
            time.revision,
            time.speed,
            observer.latitude,
            observer.longitude,
            observer.elevation,
        )
        interval = self._intervals.get(obj.id)
        if interval is not None and interval.source is obj and interval.key == key:
            span = (interval.end - interval.start).total_seconds()
            offset = (time.utc - interval.start).total_seconds()
            fraction = offset / span if span else -1
            if 0 <= fraction <= 1:
                return DynamicRenderState(
                    interpolate_position(
                        interval.first.position, interval.last.position, fraction
                    ),
                    interval.first.magnitude,
                )
            if time.utc == interval.start:
                return interval.first
        # 描画用キャッシュを背景計算・架台予測の可変キャッシュと共有しない。
        model = (
            interval.model
            if interval is not None and interval.source is obj
            else copy(obj)
        )
        first = DynamicRenderState(
            model.get_position(time, observer), model.get_magnitude(time, observer)
        )
        seconds = 0.05 if isinstance(obj, Satellite) else 1.0
        # 同時に表示された天体の再計算が毎秒同じフレームへ集中しないようにする。
        seconds *= 0.5 + (sum(obj.id.encode()) % 51) / 100.0
        # 高倍速で次フレームが区間外になる場合は、無駄な未来計算をしない。
        if abs(time.speed) > seconds * 60 or time.is_paused or time.speed == 0:
            end, last = time.utc, first
        else:
            end = time.utc + timedelta(seconds=math.copysign(seconds, time.speed))
            future = Time(utc=end, speed=time.speed, revision=time.revision)
            last = DynamicRenderState(
                model.get_position(future, observer), first.magnitude
            )
        self._intervals[obj.id] = _PositionInterval(
            obj, model, key, time.utc, end, first, last
        )
        return first
