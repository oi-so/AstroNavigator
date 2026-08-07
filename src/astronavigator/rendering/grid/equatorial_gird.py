from __future__ import annotations

from bisect import bisect_right
from typing import Iterable
from collections import OrderedDict

from astronavigator.rendering.grid.coordinate_grid import CoordinateGrid
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext
from astronavigator.sky.position import Position


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




class EquatorialGrid(CoordinateGrid[Position]):
    @property
    def coordinate_system(self) -> CoordinateSystem:
        return CoordinateSystem.EQUATORIAL


    def iter_lines(self, context: RendererContext) -> Iterable[Iterable[Position]]:
        min_pos, max_pos = context.projection.visible_bounds(context.projection_context, context.viewport.size())

        ra_interval, dec_interval = self._get_grid_intervals(context.scene.sky_camera.fov_deg)

        ra = (min_pos.ra_deg // ra_interval) * ra_interval

        while ra <= max_pos.ra_deg:
            yield self._iter_ra_line(ra, min_pos.dec_deg, max_pos.dec_deg, dec_interval)
            ra += ra_interval

        dec = (min_pos.dec_deg // dec_interval) * dec_interval
        while dec <= max_pos.dec_deg:
            yield self._iter_dec_line(dec, min_pos.ra_deg, max_pos.ra_deg, ra_interval)
            dec += dec_interval

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

    def _get_grid_intervals(self, fov_deg: float) -> tuple[float, float]:
        index = bisect_right(SORTED_GRID_INTERVAL_KEYS, fov_deg)
        if index == 0:
            return GRID_INTERVAL_TABLE[SORTED_GRID_INTERVAL_KEYS[0]]
        elif index >= len(SORTED_GRID_INTERVAL_KEYS):
            return GRID_INTERVAL_TABLE[SORTED_GRID_INTERVAL_KEYS[-1]]
        else:
            return GRID_INTERVAL_TABLE[SORTED_GRID_INTERVAL_KEYS[index - 1]]
