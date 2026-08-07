from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable
from collections.abc import Generator
from PySide6.QtCore import QPointF, QSize

from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer
from astronavigator.rendering.projection.projection import Projection
from astronavigator.scene.scene import Scene
from astronavigator.sky.position import HorizontalPosition


@dataclass(slots=True)
class HorizontalLinearProjectionContext:
    center: HorizontalPosition
    fov_deg: float
    rotate_deg: float



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
        time = scene.time
        observer = scene.observer
        skyfield = scene.skyfield

        if skyfield is None:
            raise ValueError("Skyfield context is not available in the scene.")

        horizontal_center = CoordinateTransformer.equatorial_to_horizontal(camera.center, time, observer, skyfield)

        return HorizontalLinearProjectionContext(
            center=horizontal_center,
            fov_deg=camera.fov_deg,
            rotate_deg=camera.rotation
        )