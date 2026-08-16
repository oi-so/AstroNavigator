from __future__ import annotations

from bisect import bisect_right
from typing import Iterable
from collections import OrderedDict

from astronavigator.rendering.grid.coordinate_grid import CoordinateGrid, GridLine, calculate_grid_sample_interval, format_grid_degree
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext
from astronavigator.sky.coordinate_format import RightAscensionFormat
from astronavigator.sky.position import Position
from astronavigator.utils.coordinate_formatter import format_ra_hms


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


    def iter_lines(self, context: RendererContext) -> Iterable[GridLine[Position]]:
        min_pos, max_pos = self._visible_bounds(context)

        ra_interval, dec_interval = self._get_grid_intervals(context.scene.sky_camera.fov_deg)

        ra_sample_interval = calculate_grid_sample_interval(ra_interval)
        dec_sample_interval = calculate_grid_sample_interval(dec_interval)

        ra = (min_pos.ra_deg // ra_interval) * ra_interval

        while ra <= max_pos.ra_deg:
            yield GridLine(
                positions=self._iter_ra_line(ra, min_pos.dec_deg, max_pos.dec_deg, dec_sample_interval),
                label=self._format_ra_label(ra, ra_interval, context.scene.rendering_settings.ra_format)
            )
            ra += ra_interval

        dec = (min_pos.dec_deg // dec_interval) * dec_interval
        while dec <= max_pos.dec_deg:
            yield GridLine(
                positions=self._iter_dec_line(dec, min_pos.ra_deg, max_pos.ra_deg, ra_sample_interval),
                label=format_grid_degree(dec, dec_interval, signed=True)
            )
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

    def _visible_bounds(self, context: RendererContext) -> tuple[Position, Position]:
        camera = context.scene.sky_camera
        viewport_size = context.viewport.size()
        scale = min(viewport_size.width(), viewport_size.height()) / camera.fov_deg

        half_width_deg = (viewport_size.width() / 2) / scale
        half_height_deg = (viewport_size.height() / 2) / scale

        return (
            Position(camera.center.ra_deg - half_width_deg, camera.center.dec_deg - half_height_deg),
            Position(camera.center.ra_deg + half_width_deg, camera.center.dec_deg + half_height_deg),
        )

    @staticmethod
    def _format_ra_label(ra_deg: float, interval: float, ra_format: RightAscensionFormat) -> str:
        normalized_ra = ra_deg % 360
        if ra_format == RightAscensionFormat.HMS:
            show_seconds = interval < 0.5
            return format_ra_hms(normalized_ra, show_seconds=show_seconds)
        else:
            return format_grid_degree(normalized_ra, interval)