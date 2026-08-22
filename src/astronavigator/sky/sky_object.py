from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import math
from typing import ClassVar, Any
from skyfield import almanac
from skyfield.api import wgs84, EarthSatellite
from skyfield.magnitudelib import planetary_magnitude
from datetime import datetime, timedelta

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.moon_phase import MoonPhaseInfo
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.spectral_type import SpectralType
from astronavigator.sky.dso_type import DeepSkyObjectType


@dataclass(slots=True, frozen=True)
class SatelliteBrightness:
    magnitude: Magnitude
    is_sunlit: bool
    range_km: float
    phase_angle_deg: float


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

    def get_add_info(self) -> str:
        other_names = f"ID: {self.id}" if self.id else ""
        other_names += f", HIP{self.hip}" if self.hip is not None else ""
        other_names += f", 別名: {', '.join(self.aliases)}" if self.aliases else ""
        return other_names


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
    ephemeris: Any

    standard_magnitude: float = 10.0

    is_dynamic: ClassVar[bool] = True

    _cache_key: tuple[object, ...] | None = field(default=None, init=False, repr=False)
    _cached_position: Position | None = field(default=None, init=False, repr=False)

    _brightness_cache_key: tuple[object, ...] | None = field(default=None, init=False, repr=False)
    _cached_brightness: SatelliteBrightness | None = field(default=None, init=False, repr=False)

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
        if time is None or observer is None:
            raise ValueError("Time and observer must be provided for Satellite magnitude calculation.")

        return self.get_brightness_info(time, observer).magnitude


    def get_brightness_info(self, time: Time, observer: Observer) -> SatelliteBrightness:
        time_bucket = int(time.utc.timestamp() * 20.0) # 0.05sごとにキャッシュ
        cache_key = (time_bucket, observer.latitude, observer.longitude, observer.elevation)

        if cache_key == self._brightness_cache_key and self._cached_brightness is not None:
            return self._cached_brightness

        skyfield_time = self.timescale.from_datetime(time.utc)
        observing_site = wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)

        satellite_geocentric = self.model.at(skyfield_time)
        observer_geocentric = observing_site.at(skyfield_time)

        earth = self.ephemeris["earth"]
        sun = self.ephemeris["sun"]

        sun_geocentric = (sun - earth).at(skyfield_time)

        satellite_vector = satellite_geocentric.position.km
        observer_vector = observer_geocentric.position.km
        sun_vector = sun_geocentric.position.km

        to_observer = (
            observer_vector[0] - satellite_vector[0],
            observer_vector[1] - satellite_vector[1],
            observer_vector[2] - satellite_vector[2],
        )

        to_sun = (
            sun_vector[0] - satellite_vector[0],
            sun_vector[1] - satellite_vector[1],
            sun_vector[2] - satellite_vector[2],
        )

        observer_distance = math.sqrt(to_observer[0] ** 2 + to_observer[1] ** 2 + to_observer[2] ** 2)
        sun_distance = math.sqrt(to_sun[0] ** 2 + to_sun[1] ** 2 + to_sun[2] ** 2)

        cos = to_observer[0] * to_sun[0] + to_observer[1] * to_sun[1] + to_observer[2] * to_sun[2]
        cos /= (observer_distance * sun_distance)
        cos = max(-1.0, min(1.0, cos))
        phase_angle = math.acos(cos)

        is_sunlit = bool(satellite_geocentric.is_sunlit(self.ephemeris))

        if not is_sunlit:
            magnitude = Magnitude(float(99.0))
        else:
            phase_function = math.sin(phase_angle) + (math.pi - phase_angle) * math.cos(phase_angle)
            phase_function = max(1e-12, phase_function)

            magnitude_value = self.standard_magnitude + 5.0 * math.log10(observer_distance) - 2.5 * math.log10(phase_function)
            magnitude = Magnitude(float(magnitude_value))

        result = SatelliteBrightness(
            magnitude=magnitude,
            is_sunlit=is_sunlit,
            range_km=observer_distance,
            phase_angle_deg=math.degrees(phase_angle)
        )

        self._brightness_cache_key = cache_key
        self._cached_brightness = result

        return result


@dataclass(slots=True)
class Comet(SkyObject):
    model: Any
    heliocentric_model: Any
    ephemeris: Any
    timescale: Any

    magnitude_g: float
    magnitude_k: float

    is_dynamic: ClassVar[bool] = True

    _cache_key: tuple[object, ...] | None = field(default=None, init=False, repr=False)
    _cached_apparent: Any = field(default=None, init=False, repr=False)
    _cached_heliocentric_distance_au: float | None = field(default=None, init=False, repr=False)

    def _update_cache(self, time: Time, observer: Observer) -> None:
        cache_key = time.utc.replace(microsecond=0), observer.latitude, observer.longitude, observer.elevation

        if cache_key == self._cache_key and self._cached_apparent is not None and self._cached_heliocentric_distance_au is not None:
            return

        skyfield_time = self.timescale.from_datetime(time.utc)
        geographic_position = wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)

        earth = self.ephemeris["earth"]
        topos = earth + geographic_position
        self._cached_apparent = topos.at(skyfield_time).observe(self.model).apparent()
        self._cached_heliocentric_distance_au = float(self.heliocentric_model.at(skyfield_time).distance().au)

        self._cache_key = cache_key

    def get_position(self, time: Time | None = None, observer: Observer | None = None) -> Position:
        if time is None or observer is None:
            raise ValueError("Time and observer must be provided for Comet position calculation.")

        self._update_cache(time, observer)
        apparent = self._cached_apparent
        if apparent is None:
            raise RuntimeError("Cached apparent position is not available.")
        ra, dec, _ = apparent.radec()
        return Position(float(ra.degrees), float(dec.degrees)).normalized()
    
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        if time is None or observer is None:
            raise ValueError("Time and observer must be provided for Comet magnitude calculation.")

        self._update_cache(time, observer)

        apparent = self._cached_apparent
        heliocentric_distance_au = self._cached_heliocentric_distance_au
        if apparent is None or heliocentric_distance_au is None:
            raise RuntimeError("Cached apparent position or heliocentric distance is not available.")

        observer_distance_au = float(apparent.distance().au)
        observer_distance_au = max(observer_distance_au, 1e-9)
        heliocentric_distance_au = max(heliocentric_distance_au, 1e-9)
        # 概算の等級式 m = g + 5 * log10(Δ) + k * log10(r) (g, kは定数、Δは観測値と彗星の距離、rは太陽と彗星の距離)
        magnitude = self.magnitude_g + 5.0 * math.log10(observer_distance_au) + self.magnitude_k * math.log10(heliocentric_distance_au)

        return Magnitude(float(magnitude))


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

    def get_add_info(self) -> str:
        info = f"type: {self.dso_type.name}"
        if self.major_axis_arcmin is not None and self.minor_axis_arcmin is not None:
            info += f"\n角径: {self.major_axis_arcmin:.1f}' x {self.minor_axis_arcmin:.1f}'"
        if self.position_angle_deg is not None:
            info += f", 位置角: {self.position_angle_deg:.1f}°\n"
        info += super(DeepSkyObject, self).get_add_info()
        return info

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
    _phase_cache_key: int | None = field(default=None, init=False, repr=False)
    _cached_phase_info: MoonPhaseInfo | None = field(default=None, init=False, repr=False)
    _cached_bright_limb_position: Position | None = field(default=None, init=False, repr=False)
    _previous_new_moon_utc: datetime | None = field(default=None, init=False, repr=False)
    _next_new_moon_utc: datetime | None = field(default=None, init=False, repr=False)

    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        return Magnitude(-12.74)

    def get_phase_info(self, time: Time, observer: Observer) -> MoonPhaseInfo:
        cache_key = int(time.utc.timestamp() // 60)  # 1分ごとにキャッシュ
        if cache_key == self._phase_cache_key and self._cached_phase_info is not None:
            return self._cached_phase_info

        skyfield_time = self.timescale.from_datetime(time.utc)
        illuminated_fraction = float(almanac.fraction_illuminated(self.ephemeris, "moon", skyfield_time))
        phase_angle_deg = float(almanac.moon_phase(self.ephemeris, skyfield_time).degrees) % 360.0
        previous_new_moon = self._get_previous_new_moon(time.utc)
        age_days = (time.utc - previous_new_moon).total_seconds() / 86400.0

        phase_info = MoonPhaseInfo(
            illuminated_fraction=illuminated_fraction,
            age_days=age_days,
            phase_angle_deg=phase_angle_deg,
            phase_name=self._get_phase_name(phase_angle_deg),
            is_waxing=phase_angle_deg < 180.0,
        )

        self._phase_cache_key = cache_key
        self._cached_phase_info = phase_info
        self._cached_bright_limb_position = None

        return phase_info


    def get_bright_limb_position(self, time: Time, observer: Observer) -> Position:
        self.get_phase_info(time, observer)
        if self._cached_bright_limb_position is not None:
            return self._cached_bright_limb_position

        moon_apparent = self._get_apparent(time, observer)
        skyfield_time = self.timescale.from_datetime(time.utc)
        geographic_position = wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)

        earth = self.ephemeris["earth"]
        sun = self.ephemeris["sun"]
        topos = earth + geographic_position

        sun_apparent = topos.at(skyfield_time).observe(sun).apparent()

        moon_ra, moon_dec, _ = moon_apparent.radec()
        sun_ra, sun_dec, _ = sun_apparent.radec()

        moon_vector = self._position_to_vector(float(moon_ra.radians), float(moon_dec.radians))
        sun_vector = self._position_to_vector(float(sun_ra.radians), float(sun_dec.radians))

        dot = sum(moon_component * sun_component for moon_component, sun_component in zip(moon_vector, sun_vector, strict=True))
        tan = (
            sun_vector[0] - dot * moon_vector[0],
            sun_vector[1] - dot * moon_vector[1],
            sun_vector[2] - dot * moon_vector[2],
        )

        tanget_length = math.sqrt(tan[0] ** 2 + tan[1] ** 2 + tan[2] ** 2)

        if tanget_length < 1e-10:
            position = Position(float(moon_ra.degrees), float(moon_dec.degrees) + 0.25).normalized()
            self._cached_bright_limb_position = position
            return position

        tan = (tan[0] / tanget_length, tan[1] / tanget_length, tan[2] / tanget_length)
        offset_rad = math.radians(0.25)

        reference_vector = (
            math.cos(offset_rad) * moon_vector[0] + math.sin(offset_rad) * tan[0],
            math.cos(offset_rad) * moon_vector[1] + math.sin(offset_rad) * tan[1],
            math.cos(offset_rad) * moon_vector[2] + math.sin(offset_rad) * tan[2],
        )

        position = self._vector_to_position(reference_vector)
        self._cached_bright_limb_position = position

        return position

    def _get_previous_new_moon(self, utc: datetime) -> datetime:
        if self._previous_new_moon_utc is not None and self._next_new_moon_utc is not None and self._previous_new_moon_utc <= utc < self._next_new_moon_utc:
            return self._previous_new_moon_utc

        start = self.timescale.from_datetime(utc - timedelta(days=40))
        end = self.timescale.from_datetime(utc + timedelta(days=40))

        phase_times, phase_types = almanac.find_discrete(start, end, almanac.moon_phases(self.ephemeris))
        new_moons = [phase_time.utc_datetime() for phase_time, phase_type in zip(phase_times, phase_types, strict=True) if int(phase_type) == 0]

        previous_new_moons = [value for value in new_moons if value <= utc]
        next_new_moons = [value for value in new_moons if value > utc]

        if not previous_new_moons or not next_new_moons:
            raise RuntimeError("Failed to find previous or next new moon.")

        self._previous_new_moon_utc = max(previous_new_moons)
        self._next_new_moon_utc = min(next_new_moons)

        return self._previous_new_moon_utc

    @staticmethod
    def _get_phase_name(phase_angle_deg: float) -> str:
        if phase_angle_deg < 22.5:
            return "新月"
        elif phase_angle_deg < 67.5:
            return "三日月"
        elif phase_angle_deg < 112.5:
            return "上弦"
        elif phase_angle_deg < 157.5:
            return "十三夜"
        elif phase_angle_deg < 202.5:
            return "満月"
        elif phase_angle_deg < 247.5:
            return "十六夜"
        elif phase_angle_deg < 292.5:
            return "下弦"
        elif phase_angle_deg < 337.5:
            return "二十六夜"
        else:
            return "新月"

    @staticmethod
    def _position_to_vector(ra_deg: float, dec_deg: float) -> tuple[float, float, float]:
        ra_rad = math.radians(ra_deg)
        dec_rad = math.radians(dec_deg)
        cos_dec = math.cos(dec_rad)

        return (
            cos_dec * math.cos(ra_rad),
            cos_dec * math.sin(ra_rad),
            math.sin(dec_rad)
        )

    @staticmethod
    def _vector_to_position(vector: tuple[float, float, float]) -> Position:
        x, y, z = vector
        r = math.sqrt(x ** 2 + y ** 2 + z ** 2)
        x /= r
        y /= r
        z /= r

        ra_deg = math.degrees(math.atan2(y, x)) % 360.0
        dec_deg = math.degrees(math.asin(max(-1.0, min(1.0, z))))

        return Position(ra_deg, dec_deg).normalized()

@dataclass(slots=True)
class Planet(SolarSystemBody):
    def get_magnitude(self, time: Time | None = None, observer: Observer | None = None) -> Magnitude:
        if time is None or observer is None:
            raise ValueError("Time and observer must be provided for Planet magnitude calculation.")

        apparent = self._get_apparent(time, observer)
        return Magnitude(float(planetary_magnitude(apparent)))