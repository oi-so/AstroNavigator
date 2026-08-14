from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable
from collections.abc import Generator
from PySide6.QtCore import QPointF, QSize

from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.projection.projection import Projection
from astronavigator.scene.observer import Observer
from astronavigator.scene.scene import Scene
from astronavigator.scene.time import Time
from astronavigator.sky.position import HorizontalPosition, Position
from astronavigator.sky.sky_object import SkyObject


@dataclass(slots=True)
class LinearProjectionContext:
    center: Position
    fov_deg: float
    rotate_deg: float
    time: Time
    observer: Observer
    skyfield: Any


class LinearProjection(Projection[Position, LinearProjectionContext]):
    def project(
        self, 
        position: Position, 
        context: LinearProjectionContext, 
        viewport_size: QSize
    ) -> QPointF | None:
        delta_ra = position.ra_deg - context.center.ra_deg
        delta_ra = ((delta_ra + 180) % 360) - 180
        delta_dec = position.dec_deg - context.center.dec_deg

        width = viewport_size.width()
        height = viewport_size.height()

        scale = min(width, height) / context.fov_deg

        x = width / 2 + delta_ra * scale
        y = height / 2 - delta_dec * scale

        if x < 0 or x > width or y < 0 or y > height:
            return None
        
        # TODO: Apply camera rotation
        
        return QPointF(x, y)


    def unproject(
        self, 
        screen_position: QPointF, 
        context: LinearProjectionContext, 
        viewport_size: QSize
    ) -> Position:
        raise NotImplementedError("Orthographic unprojection is not implemented yet.")


    def visible_bounds(self, context: LinearProjectionContext, viewport_size: QSize) -> tuple[Position, Position]:
        width = viewport_size.width()
        height = viewport_size.height()

        scale = min(width, height) / context.fov_deg

        half_width_deg = (width / 2) / scale
        half_height_deg = (height / 2) / scale

        min_ra = context.center.ra_deg - half_width_deg
        max_ra = context.center.ra_deg + half_width_deg
        min_dec = context.center.dec_deg - half_height_deg
        max_dec = context.center.dec_deg + half_height_deg

        return Position(min_ra, min_dec), Position(max_ra, max_dec)


    def iter_grid_lines(self, context: LinearProjectionContext, viewport_size: QSize, interval: float) -> Generator[tuple[float, Iterable[Position]], None, None]:
        yield from self.iter_ra_lines(context, viewport_size, interval)
        yield from self.iter_dec_lines(context, viewport_size, interval)


    def iter_ra_lines(self, context: LinearProjectionContext, viewport_size: QSize, interval_deg: float) -> Generator[tuple[float, Iterable[Position]], None, None]:
        min_pos, max_pos = self.visible_bounds(context, viewport_size)
        start_ra = math.floor(min_pos.ra_deg / interval_deg) * interval_deg
    
        ra = start_ra
        while ra <= max_pos.ra_deg:
            yield (ra, self._iter_ra_line(ra, min_pos.dec_deg - interval_deg, max_pos.dec_deg + interval_deg, interval_deg))
            ra += interval_deg

    def iter_dec_lines(self, context: LinearProjectionContext, viewport_size: QSize, interval_deg: float) -> Generator[tuple[float, Iterable[Position]], None, None]:
        min_pos, max_pos = self.visible_bounds(context, viewport_size)
        start_dec = math.floor(min_pos.dec_deg / interval_deg) * interval_deg
    
        dec = start_dec
        while dec <= max_pos.dec_deg:
            yield (dec, self._iter_dec_line(dec, min_pos.ra_deg - interval_deg, max_pos.ra_deg + interval_deg, interval_deg))
            dec += interval_deg


    def _iter_ra_line(self, ra: float, min_dec: float, max_dec: float, dec_interval: float) -> Iterable[Position]:
        dec = min_dec
        while dec <= max_dec:
            yield Position(ra, dec)
            dec += dec_interval

    def _iter_dec_line(self, dec: float, min_ra: float, max_ra: float, ra_interval: float) -> Iterable[Position]:
        ra = min_ra
        while ra <= max_ra:
            yield Position(ra, dec)
            ra += ra_interval



    def create_context(self, scene: Scene) -> LinearProjectionContext:
        camera = scene.sky_camera
        return LinearProjectionContext(
            center=camera.center,
            fov_deg=camera.fov_deg,
            rotate_deg=camera.rotation,
            time=scene.time,
            observer=scene.observer,
            skyfield=scene.skyfield
        )


    def project_object(self, obj: SkyObject, context: LinearProjectionContext, viewport_size: QSize) -> QPointF | None:
        position = obj.get_position(context.time, context.observer)
        return self.project(position, context, viewport_size)

    def project_grid_position(
        self,
        position: Position | HorizontalPosition,
        coordinate_system: CoordinateSystem,
        context: LinearProjectionContext,
        viewport_size: QSize
    ) -> QPointF | None:
        if coordinate_system == CoordinateSystem.EQUATORIAL and isinstance(position, Position):
            return self.project(position, context, viewport_size)

        if coordinate_system == CoordinateSystem.HORIZONTAL and isinstance(position, HorizontalPosition):
            if context.skyfield is None:
                return None

            equatorial_position = CoordinateTransformer.horizontal_to_equatorial(
                position,
                context.time,
                context.observer,
                context.skyfield
            )
            return self.project(equatorial_position, context, viewport_size)

        return None

    
    def convert_position(self, position: Position, context: LinearProjectionContext) -> Position:
        return position