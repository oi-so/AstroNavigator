from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Iterable, Any
from collections.abc import Generator
from PySide6.QtCore import QPointF, QSize
from skyfield.api import wgs84

from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.projection.projection import Projection
from astronavigator.scene.observer import Observer
from astronavigator.scene.scene import Scene
from astronavigator.scene.time import Time
from astronavigator.sky.position import HorizontalPosition, Position
from astronavigator.sky.sky_object import SkyObject



@dataclass(slots=True)
class HorizontalLinearProjectionContext:
    center: HorizontalPosition
    fov_deg: float
    rotate_deg: float
    time: Time
    observer: Observer
    skyfield: Any
    topos: Any
    skyfield_time: Any
    observer_position: Any
    _position_cache: dict[Position, HorizontalPosition] = field(default_factory=dict)


class HorizontalLinearProjection(Projection[HorizontalPosition, HorizontalLinearProjectionContext]):
    def project(
        self, 
        position: HorizontalPosition, 
        context: HorizontalLinearProjectionContext, 
        viewport_size: QSize
    ) -> QPointF | None:
        delta_az = (position.azimuth_deg - context.center.azimuth_deg + 180) % 360 - 180
        delta_alt = position.altitude_deg - context.center.altitude_deg

        width = viewport_size.width()
        height = viewport_size.height()

        scale = min(width, height) / context.fov_deg

        x = width / 2 + delta_az * scale
        y = height / 2 - delta_alt * scale

        if x < 0 or x > width or y < 0 or y > height:
            return None
        
        # TODO: Apply camera rotation
        
        return QPointF(x, y)


    def unproject(
        self, 
        screen_position: QPointF, 
        context: HorizontalLinearProjectionContext, 
        viewport_size: QSize
    ) -> HorizontalPosition:
        raise NotImplementedError("Orthographic unprojection is not implemented yet.")


    def visible_bounds(self, context: HorizontalLinearProjectionContext, viewport_size: QSize) -> tuple[HorizontalPosition, HorizontalPosition]:
        width = viewport_size.width()
        height = viewport_size.height()

        scale = min(width, height) / context.fov_deg

        half_width_deg = (width / 2) / scale
        half_height_deg = (height / 2) / scale

        min_az = context.center.azimuth_deg - half_width_deg
        max_az = context.center.azimuth_deg + half_width_deg
        min_alt = context.center.altitude_deg - half_height_deg
        max_alt = context.center.altitude_deg + half_height_deg

        return HorizontalPosition(min_az, min_alt), HorizontalPosition(max_az, max_alt)


    def iter_az_lines(self, context: HorizontalLinearProjectionContext, viewport_size: QSize, interval_deg: float) -> Generator[tuple[float, Iterable[HorizontalPosition]], None, None]:
        min_pos, max_pos = self.visible_bounds(context, viewport_size)
        start_az = math.floor(min_pos.azimuth_deg / interval_deg) * interval_deg
    
        az = start_az
        while az <= max_pos.azimuth_deg:
            yield (az, self._iter_az_line(az, min_pos.altitude_deg - interval_deg, max_pos.altitude_deg + interval_deg, interval_deg))
            az += interval_deg

    def iter_alt_lines(self, context: HorizontalLinearProjectionContext, viewport_size: QSize, interval_deg: float) -> Generator[tuple[float, Iterable[HorizontalPosition]], None, None]:
        min_pos, max_pos = self.visible_bounds(context, viewport_size)
        start_alt = math.floor(min_pos.altitude_deg / interval_deg) * interval_deg
    
        alt = start_alt
        while alt <= max_pos.altitude_deg:
            yield (alt, self._iter_alt_line(alt, min_pos.azimuth_deg - interval_deg, max_pos.azimuth_deg + interval_deg, interval_deg))
            alt += interval_deg


    def _iter_az_line(self, az: float, min_alt: float, max_alt: float, alt_interval: float) -> Iterable[HorizontalPosition]:
        alt = min_alt
        while alt <= max_alt:
            yield HorizontalPosition(az, alt)
            alt += alt_interval

    def _iter_alt_line(self, alt: float, min_az: float, max_az: float, az_interval: float) -> Iterable[HorizontalPosition]:
        az = min_az
        while az <= max_az:
            yield HorizontalPosition(az, alt)
            az += az_interval



    def create_context(self, scene: Scene) -> HorizontalLinearProjectionContext:
        camera = scene.sky_camera
        center = camera.center
        time = scene.time
        observer = scene.observer
        context = scene.skyfield

        if context is None:
            raise ValueError("Skyfield context is not available in the scene.")

        earth = context.ephemeris["earth"]
        topos = earth + wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)
        skyfield_time = context.timescale.from_datetime(time.utc)
        observer_position = topos.at(skyfield_time)

        return HorizontalLinearProjectionContext(
            center=CoordinateTransformer.equatorial_to_horizontal(center, observer_position),
            fov_deg=camera.fov_deg,
            rotate_deg=camera.rotation,
            time=time,
            observer=observer,
            skyfield=context,
            topos=topos,
            skyfield_time=skyfield_time,
            observer_position=topos.at(skyfield_time)
        )


    def project_object(self, obj: SkyObject, context: HorizontalLinearProjectionContext, viewport_size: QSize) -> QPointF | None:
        position = CoordinateTransformer.equatorial_to_horizontal(obj.get_position(context.time, context.observer), context.observer_position)
        return self.project(position, context, viewport_size)

    def project_grid_position(
        self,
        position: Position | HorizontalPosition,
        coordinate_system: CoordinateSystem,
        context: HorizontalLinearProjectionContext,
        viewport_size: QSize
    ) -> QPointF | None:
        if coordinate_system == CoordinateSystem.HORIZONTAL and isinstance(position, HorizontalPosition):
            return self.project(position, context, viewport_size)

        if coordinate_system == CoordinateSystem.EQUATORIAL and isinstance(position, Position):
            horizontal_position = self.convert_position(position, context)
            return self.project(horizontal_position, context, viewport_size)

        return None

    def iter_grid_lines(self, context: HorizontalLinearProjectionContext, viewport_size: QSize, interval: float) -> Generator[tuple[float, Iterable[HorizontalPosition]], None, None]:
        yield from self.iter_az_lines(context, viewport_size, interval)
        yield from self.iter_alt_lines(context, viewport_size, interval)


    def convert_position(self, position: Position, context: HorizontalLinearProjectionContext) -> HorizontalPosition:
        key = (position.ra_deg, position.dec_deg)
        cached = context._position_cache.get(key)
        if cached is not None:
            return cached

        converted = CoordinateTransformer.equatorial_to_horizontal(position, context.observer_position)
        context._position_cache[key] = converted
        return converted