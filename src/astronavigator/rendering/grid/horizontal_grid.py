from __future__ import annotations

from bisect import bisect_right
from collections.abc import Iterable
from typing import OrderedDict
import math

from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer
from astronavigator.rendering.grid.coordinate_grid import CoordinateGrid, GridLabelPlacement, GridLine, GridPointLabel, calculate_grid_sample_interval, calculate_parallel_sample_interval, calculate_spherical_longitude_bounds, format_grid_degree
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext
from astronavigator.sky.position import HorizontalPosition


ZENITH_MINOR_LINE_LIMIT_DEG = 80.0
ZENITH_MEDIUM_LINE_LIMIT_DEG = 85.0

MEDIUM_AZ_INTERVAL_DEG = 30.0
MAJOR_AZ_INTERVAL_DEG = 90.0

ANGLE_EPSILON = 1e-9

CARDINAL_LABEL_FOV = 120.0
CARDINAL_LABEL_DIRECTION_ALTITUDE_DEG = 1.0

CARDINAL_LABELS = {
    0.0: "北",
    90.0: "東",
    180.0: "南",
    270.0: "西",
}


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


    def iter_lines(self, context: RendererContext) -> Iterable[GridLine[HorizontalPosition]]:
        bounds = self._visible_bounds(context)
        if bounds is None:
            return

        min_pos, max_pos = bounds

        az_interval, alt_interval = self._get_grid_intervals(context.scene.sky_camera.fov_deg)

        fov_deg = context.scene.sky_camera.fov_deg
        alt_sample_interval = calculate_grid_sample_interval(alt_interval, fov_deg)

        raw_min_alt = min_pos.altitude_deg
        raw_max_alt = max_pos.altitude_deg

        min_alt = max(-90.0, raw_min_alt)
        max_alt = min(90.0, raw_max_alt)

        min_az = min_pos.azimuth_deg
        max_az = max_pos.azimuth_deg

        includes_zenith_or_nadir = raw_min_alt <= -90.0 or raw_max_alt >= 90.0
        if includes_zenith_or_nadir:
            min_az = 0.0
            max_az = 360.0

        az = (min_az // az_interval) * az_interval
        while az <= max_az + ANGLE_EPSILON:
            if includes_zenith_or_nadir and az >= 360.0 - ANGLE_EPSILON:
                break
            line_alt_bounds = self._calculate_az_line_alt_bounds(az, min_alt, max_alt, includes_zenith_or_nadir)

            if line_alt_bounds is not None:
                line_min_alt, line_max_alt = line_alt_bounds
                yield GridLine(
                    positions=self._iter_az_line(az, line_min_alt, line_max_alt, alt_sample_interval),
                    label=format_grid_degree(az, az_interval),
                    label_placement=GridLabelPlacement.TOP_BOTTOM
                )
            az += az_interval

        alt = (min_alt // alt_interval) * alt_interval
        while alt <= max_alt + ANGLE_EPSILON:
            if abs(alt) < 90.0 - ANGLE_EPSILON:
                line_az_sample_interval = calculate_parallel_sample_interval(alt_interval, alt, max_az - min_az)
                yield GridLine(
                    positions=self._iter_alt_line(alt, min_az, max_az, line_az_sample_interval),
                    label=format_grid_degree(alt, alt_interval, signed=True),
                    label_placement=GridLabelPlacement.LEFT_RIGHT
                )
            alt += alt_interval

    def _iter_az_line(self, az: float, min_alt: float, max_alt: float, alt_interval: float) -> Iterable[HorizontalPosition]:
        yield HorizontalPosition(az, min_alt)
        alt = min_alt + alt_interval
        while alt < max_alt - ANGLE_EPSILON:
            yield HorizontalPosition(az, alt)
            alt += alt_interval
        if max_alt > min_alt + ANGLE_EPSILON:
            yield HorizontalPosition(az, max_alt)

    def _iter_alt_line(self, alt: float, min_az: float, max_az: float, az_interval: float) -> Iterable[HorizontalPosition]:
        yield HorizontalPosition(min_az, alt)
        az = min_az + az_interval

        while az < max_az - ANGLE_EPSILON:
            yield HorizontalPosition(az, alt)
            az += az_interval

        if max_az > min_az + ANGLE_EPSILON:
            yield HorizontalPosition(max_az, alt)

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
        half_fov_deg = camera.fov_deg / 2.0

        min_az, max_az = calculate_spherical_longitude_bounds(
            center.azimuth_deg, center.altitude_deg, half_fov_deg
        )

        return (
            HorizontalPosition(min_az, center.altitude_deg - half_fov_deg),
            HorizontalPosition(max_az, center.altitude_deg + half_fov_deg),
        )


    def _calculate_az_line_alt_bounds(self, az: float, min_alt: float, max_alt: float, includes_zenith_or_nadir: bool) -> tuple[float, float] | None:
        if not includes_zenith_or_nadir:
            return (min_alt, max_alt)

        normalized_az = az % 360.0

        if self._is_angle_multiple(normalized_az, MAJOR_AZ_INTERVAL_DEG):
            limit = 90.0
        elif self._is_angle_multiple(normalized_az, MEDIUM_AZ_INTERVAL_DEG):
            limit = ZENITH_MEDIUM_LINE_LIMIT_DEG
        else:
            limit = ZENITH_MINOR_LINE_LIMIT_DEG

        line_min_alt = max(min_alt, -limit)
        line_max_alt = min(max_alt, limit)

        if line_min_alt > line_max_alt + ANGLE_EPSILON:
            return None

        return (line_min_alt, line_max_alt)

    @staticmethod
    def _is_angle_multiple(angle: float, interval: float) -> bool:
        remainder = angle % interval
        return (
            math.isclose(remainder, 0.0, abs_tol=ANGLE_EPSILON) or
            math.isclose(remainder, interval, abs_tol=ANGLE_EPSILON)
        )


    def iter_point_labels(self, context: RendererContext) -> Iterable[GridPointLabel[HorizontalPosition]]:
        if context.scene.sky_camera.fov_deg < CARDINAL_LABEL_FOV:
            return ()

        for az, text in CARDINAL_LABELS.items():
            yield GridPointLabel(
                position=HorizontalPosition(az, 0.0),
                offset_position=HorizontalPosition(az, CARDINAL_LABEL_DIRECTION_ALTITUDE_DEG),
                text=text,
            )