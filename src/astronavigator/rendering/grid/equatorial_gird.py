from __future__ import annotations

from bisect import bisect_right
from typing import Iterable
from collections import OrderedDict
import math

from astronavigator.rendering.grid.coordinate_grid import CoordinateGrid, GridLabelPlacement, GridLine, calculate_grid_sample_interval, calculate_parallel_sample_interval, calculate_spherical_longitude_bounds, format_grid_degree, calculate_longitude_grid_interval
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext
from astronavigator.sky.coordinate_format import RightAscensionFormat
from astronavigator.sky.position import Position
from astronavigator.utils.coordinate_formatter import format_ra_hms


POLE_MINOR_LINE_LIMIT_DEG = 80.0
POLE_MEDIUM_LINE_LIMIT_DEG = 85.0

MEDIUM_RA_INTERVAL_DEG = 30.0
MAJOR_RA_INTERVAL_DEG = 90.0

ANGLE_EPSILON = 1e-9


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
        raw_min_dec = min_pos.dec_deg
        raw_max_dec = max_pos.dec_deg

        min_dec = max(-90.0, raw_min_dec)
        max_dec = min(90.0, raw_max_dec)

        includes_pole = raw_min_dec <= -90.0 or raw_max_dec >= 90.0
        if includes_pole:
            min_ra = 0.0
            max_ra = 360.0
        else:
            min_ra = min_pos.ra_deg
            max_ra = max_pos.ra_deg

        base_ra_interval, dec_interval = self._get_grid_intervals(context.scene.sky_camera.fov_deg)
        ra_interval = calculate_longitude_grid_interval(base_ra_interval, max_ra - min_ra)

        fov_deg = context.scene.sky_camera.fov_deg
        dec_sample_interval = calculate_grid_sample_interval(dec_interval, fov_deg)

        ra = (min_ra // ra_interval) * ra_interval
        while ra <= max_ra + ANGLE_EPSILON:
            if includes_pole and ra >= 360.0 - ANGLE_EPSILON:
                break

            line_min_dec, line_max_dec = self._calculate_ra_line_dec_bounds(
                ra, min_dec, max_dec, includes_pole
            )

            if line_min_dec <= line_max_dec:
                yield GridLine(
                    positions=self._iter_ra_line(ra, line_min_dec, line_max_dec, dec_sample_interval),
                    label=self._format_ra_label(ra, ra_interval, context.scene.rendering_settings.ra_format),
                    label_placement=GridLabelPlacement.TOP_BOTTOM
                )
            ra += ra_interval

        dec = (min_dec // dec_interval) * dec_interval
        while dec <= max_dec + ANGLE_EPSILON:
            if abs(dec) < 90.0 - ANGLE_EPSILON:
                line_ra_sample_interval = calculate_parallel_sample_interval(base_ra_interval, dec, max_ra - min_ra)
                yield GridLine(
                    positions=self._iter_dec_line(dec, min_ra, max_ra, line_ra_sample_interval),
                    label=format_grid_degree(dec, dec_interval, signed=True),
                    label_placement=GridLabelPlacement.LEFT_RIGHT
                )
            dec += dec_interval

    def _iter_ra_line(self, ra: float, min_dec: float, max_dec: float, dec_interval: float) -> Iterable[Position]:
        if min_dec > max_dec:
            return
        yield Position(ra, min_dec)
        dec = min_dec + dec_interval

        while dec < max_dec - ANGLE_EPSILON:
            yield Position(ra, dec)
            dec += dec_interval

        if max_dec > min_dec + ANGLE_EPSILON:
            yield Position(ra, max_dec)

    def _iter_dec_line(self, dec: float, min_ra: float, max_ra: float, ra_interval: float) -> Iterable[Position]:
        if min_ra > max_ra:
            return
        yield Position(min_ra, dec)
        ra = min_ra + ra_interval

        while ra < max_ra - ANGLE_EPSILON:
            yield Position(ra, dec)
            ra += ra_interval

        if max_ra > min_ra + ANGLE_EPSILON:
            yield Position(max_ra, dec)
            

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
        half_fov_deg = camera.fov_deg / 2.0

        min_ra, max_ra = calculate_spherical_longitude_bounds(
            camera.center.ra_deg, camera.center.dec_deg, half_fov_deg
        )

        return (
            Position(min_ra, camera.center.dec_deg - half_fov_deg),
            Position(max_ra, camera.center.dec_deg + half_fov_deg),
        )

    @staticmethod
    def _format_ra_label(ra_deg: float, interval: float, ra_format: RightAscensionFormat) -> str:
        normalized_ra = ra_deg % 360
        if ra_format == RightAscensionFormat.HMS:
            show_seconds = interval < 0.5
            return format_ra_hms(normalized_ra, show_seconds=show_seconds)
        else:
            return format_grid_degree(normalized_ra, interval)


    @classmethod
    def _calculate_ra_line_dec_bounds(cls, ra: float, min_dec: float, max_dec: float, includes_pole: bool) -> tuple[float, float]:
        if not includes_pole:
            return min_dec, max_dec

        if cls._is_angle_multiple(ra, MAJOR_RA_INTERVAL_DEG):
            limit = 90.0
        elif cls._is_angle_multiple(ra, MEDIUM_RA_INTERVAL_DEG):
            limit = POLE_MEDIUM_LINE_LIMIT_DEG
        else:
            limit = POLE_MINOR_LINE_LIMIT_DEG

        return (max(min_dec, -limit), min(max_dec, limit))

    @staticmethod
    def _is_angle_multiple(angle: float, interval: float) -> bool:
        remainder = angle % interval
        return math.isclose(remainder, 0.0, abs_tol=ANGLE_EPSILON) or math.isclose(remainder, interval, abs_tol=ANGLE_EPSILON)