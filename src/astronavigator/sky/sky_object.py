from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Any
from skyfield.api import wgs84, EarthSatellite
from skyfield.magnitudelib import planetary_magnitude

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.spectral_type import SpectralType
from astronavigator.sky.dso_type import DeepSkyObjectType


@dataclass(slots=True)
class SkyObject(ABC):
    id: str
    name: str
    object_type: ObjectType
    hip: int | None

    aliases: tuple[str, ...] = field(default_factory=tuple, kw_only=True)

    is_dynamic: ClassVar[bool] = False

    @abstractmethod
    def get_position(self, time: Time | None = None, observer: Observer | None = None) -> Position:
        ...

    @abstractmethod
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        ...


@dataclass(slots=True)
class Star(SkyObject):
    _position: Position
    _magnitude: Magnitude
    spectral_type: SpectralType = SpectralType.UNKNOWN
    def get_position(self, time: Time | None = None, observer: Observer | None = None) -> Position:
        return self._position
    
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        return self._magnitude

@dataclass(slots=True)
class Satellite(SkyObject):
    model: EarthSatellite
    timescale: Any

    is_dynamic: ClassVar[bool] = True

    _cache_key: tuple[object, ...] | None = field(default=None, init=False, repr=False)
    _cached_position: Position | None = field(default=None, init=False, repr=False)

    def get_position(self, time: Time | None = None, observer: Observer | None = None) -> Position:
        if time is None or observer is None:
            raise ValueError("Time and observer must be provided for Satellite position calculation.")

        time_bucket = int(time.utc.timestamp() * 20.0) # 0.05sごとにキャッシュ
        cache_key = (time_bucket, observer.latitude, observer.longitude, observer.elevation)

        if cache_key == self._cache_key and self._cached_position is not None:
            return self._cached_position

        skyfield_time = self.timescale.from_datetime(time.utc)
        observing_site = wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)
        topocentric = (self.model - observing_site).at(skyfield_time)
        ra, dec, _ = topocentric.radec()

        position = Position(float(ra.degrees), float(dec.degrees)).normalized()

        self._cache_key = cache_key
        self._cached_position = position
        return position

    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        return Magnitude(0.0)  # TODO: ISSの等級計算


@dataclass(slots=True)
class Comet(SkyObject):
    is_dynamic: ClassVar[bool] = True

    def get_position(self, time: Time | None = None, observer: Observer | None = None) -> Position:
        raise NotImplementedError("Comet position calculation is not implemented yet.")
    
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        raise NotImplementedError("Comet magnitude calculation is not implemented yet.")


@dataclass(slots=True)
class DeepSkyObject(SkyObject):
    _position: Position
    _magnitude: Magnitude

    dso_type: DeepSkyObjectType = DeepSkyObjectType.OTHER
    major_axis_arcmin: float | None = None # 主軸（分）
    minor_axis_arcmin: float | None = None # 従軸（分）
    position_angle_deg: float | None = None # 位置角（度）

    def get_position(self, time: Time | None = None, observer: Observer | None = None) -> Position:
        return self._position
    
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        return self._magnitude

@dataclass(slots=True)
class Asteroid(SkyObject):
    is_dynamic: ClassVar[bool] = True
    spectral_type: SpectralType = SpectralType.UNKNOWN

    def get_position(self, time: Time | None = None, observer: Observer | None = None) -> Position:
        raise NotImplementedError("Asteroid position calculation is not implemented yet.")

    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        raise NotImplementedError("Asteroid magnitude calculation is not implemented yet.")


@dataclass(slots=True)
class SolarSystemBody(SkyObject):
    ephemeris: Any
    timescale: Any
    target_name: str

    is_dynamic: ClassVar[bool] = True

    _cache_key: tuple[object, ...] | None = field(default=None, init=False, repr=False)
    _cached_apparent: Any = field(default=None, init=False, repr=False)

    def _get_apparent(self, time: Time, observer: Observer) -> Any:
        cache_key = (
            time.utc.replace(microsecond=0), observer.latitude, observer.longitude, observer.elevation
        )

        if cache_key == self._cache_key:
            return self._cached_apparent

        skyfield_time = self.timescale.from_datetime(time.utc)
        geographic_position = wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)

        earth = self.ephemeris["earth"]
        target = self.ephemeris[self.target_name]
        topocentric_observer = earth + geographic_position

        apparent = topocentric_observer.at(skyfield_time).observe(target).apparent()

        self._cache_key = cache_key
        self._cached_apparent = apparent
        return apparent

    def get_position(self, time: Time | None = None, observer: Observer | None = None) -> Position:
        if time is None or observer is None:
            raise ValueError("Time and observer must be provided for SolarSystemBody position calculation.")
        apparent = self._get_apparent(time, observer)
        ra, dec, _ = apparent.radec()
        return Position(float(ra.degrees), float(dec.degrees))

@dataclass(slots=True)
class Sun(SolarSystemBody):
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        return Magnitude(-26.74)

@dataclass(slots=True)
class Moon(SolarSystemBody):
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        # TODO: 月の等級計算
        return Magnitude(-12.7)

@dataclass(slots=True)
class Planet(SolarSystemBody):
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        if time is None or observer is None:
            raise ValueError("Time and observer must be provided for Planet magnitude calculation.")

        apparent = self._get_apparent(time, observer)
        return Magnitude(float(planetary_magnitude(apparent)))