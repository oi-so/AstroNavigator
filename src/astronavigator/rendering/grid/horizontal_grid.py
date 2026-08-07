from __future__ import annotations

from bisect import bisect_right
from collections.abc import Iterable
from typing import OrderedDict

from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer
from astronavigator.rendering.grid.coordinate_grid import CoordinateGrid
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext
from astronavigator.sky.position import HorizontalPosition



GRID_INTERVAL_TABLE: OrderedDict[float, tuple[float, float]] = OrderedDict({
    0: (0.1, 0.1),
    0.5: (0.2, 0.2),
    1: (0.5, 0.5),
    3: (1, 1),
    7: (2, 2),
    15: (5, 5),
    30: (10, 10),
    70: (15, 15),
    120: (30, 30),
})

SORTED_GRID_INTERVAL_KEYS = sorted(GRID_INTERVAL_TABLE.keys())

class HorizontalGrid(CoordinateGrid[HorizontalPosition]):
    @property
    def coordinate_system(self) -> CoordinateSystem:
        return CoordinateSystem.HORIZONTAL


    def iter_lines(self, context: RendererContext) -> Iterable[Iterable[HorizontalPosition]]:
        bounds = self._visible_bounds(context)
        if bounds is None:
            return

        min_pos, max_pos = bounds

        az_interval, alt_interval = self._get_grid_intervals(context.scene.sky_camera.fov_deg)

        az = (min_pos.azimuth_deg // az_interval) * az_interval
        while az <= max_pos.azimuth_deg:
            yield self._iter_az_line(az, min_pos.altitude_deg, max_pos.altitude_deg, alt_interval)
            az += az_interval

        alt = (min_pos.altitude_deg // alt_interval) * alt_interval
        while alt <= max_pos.altitude_deg:
            yield self._iter_alt_line(alt, min_pos.azimuth_deg, max_pos.azimuth_deg, az_interval)
            alt += alt_interval

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

    def _get_grid_intervals(self, fov_deg: float) -> tuple[float, float]:
        index = bisect_right(SORTED_GRID_INTERVAL_KEYS, fov_deg)
        if index == 0:
            return GRID_INTERVAL_TABLE[SORTED_GRID_INTERVAL_KEYS[0]]
        elif index >= len(SORTED_GRID_INTERVAL_KEYS):
            return GRID_INTERVAL_TABLE[SORTED_GRID_INTERVAL_KEYS[-1]]
        else:
            return GRID_INTERVAL_TABLE[SORTED_GRID_INTERVAL_KEYS[index - 1]]

    def _visible_bounds(self, context: RendererContext) -> tuple[HorizontalPosition, HorizontalPosition] | None:
        if context.scene.skyfield is None:
            return None

        center = CoordinateTransformer.equatorial_to_horizontal(
            context.scene.sky_camera.center,
            context.projection_context.observer_position
        )
        camera = context.scene.sky_camera
        viewport_size = context.viewport.size()
        scale = min(viewport_size.width(), viewport_size.height()) / camera.fov_deg

        half_width_deg = (viewport_size.width() / 2) / scale
        half_height_deg = (viewport_size.height() / 2) / scale

        return (
            HorizontalPosition(center.azimuth_deg - half_width_deg, center.altitude_deg - half_height_deg),
            HorizontalPosition(center.azimuth_deg + half_width_deg, center.altitude_deg + half_height_deg),
        )
