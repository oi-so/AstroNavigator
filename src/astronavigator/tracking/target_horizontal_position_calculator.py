from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from skyfield.api import wgs84

from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer
from astronavigator.catalog.parser.skyfield_parser import SkyfieldContext
from astronavigator.scene.observer import Observer
from astronavigator.sky.position import HorizontalPosition, Position


class TargetHorizontalPositionCalculator(ABC):
    @abstractmethod
    def calculate(
        self,
        position: Position,
        time_utc: datetime,
        observer: Observer
    ) -> HorizontalPosition:
        ...



class SkyfieldHorizontalPositionCalculator(TargetHorizontalPositionCalculator):
    def __init__(self, context: SkyfieldContext) -> None:
        self._context = context

        self._observer_key: tuple[float, float, float] | None = None
        self._topocentric_observer = None


    def calculate(self, position: Position, time_utc: datetime, observer: Observer) -> HorizontalPosition:
        topocentric_observer = self._get_topocentric_observer(observer)
        skyfield_time = self._context.timescale.from_datetime(time_utc)
        observer_position = topocentric_observer.at(skyfield_time)
        return CoordinateTransformer.equatorial_to_horizontal(position, observer_position)

    def _get_topocentric_observer(self, observer: Observer) -> Any:
        observer_key = (observer.latitude, observer.longitude, observer.elevation)
        if observer_key == self._observer_key and self._topocentric_observer is not None:
            return self._topocentric_observer

        geographic_position = wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)
        self._topocentric_observer = self._context.ephemeris["earth"] + geographic_position
        self._observer_key = observer_key

        return self._topocentric_observer