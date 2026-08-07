from __future__ import annotations

from bisect import bisect_right
from typing import Iterable
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPainter, QPen
from collections import OrderedDict

from astronavigator.rendering.projection.linear_projection import LinearProjection
from astronavigator.rendering.render_context import RendererContext
from astronavigator.sky.coordinate_format import RightAscensionFormat
from astronavigator.sky.position import Position
from astronavigator.utils.coordinate_formatter import format_ra_deg, format_dec_deg, format_ra_hms


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




class EquatorialGridRenderer:
    def render(self, context: RendererContext[Position, LinearProjection]) -> None:
        self._draw_ra_grid(context)
        self._draw_dec_grid(context)
        # self._draw_celestial_equator(context)
        # self._draw_ecliptic(context)

    
    def _get_grid_interval(self, camera_fov: float) -> tuple[float, float]:
        index = bisect_right(SORTED_GRID_INTERVAL_KEYS, camera_fov)
        if index == 0:
            raise ValueError("Camera FOV is too small for grid rendering.")
        
        return GRID_INTERVAL_TABLE[SORTED_GRID_INTERVAL_KEYS[index - 1]]


    def _draw_ra_grid(self, context: RendererContext[Position, LinearProjection]) -> None:
        painter = context.painter
        scene = context.scene
        viewport = context.viewport
        projection_context = context.projection_context
        projection = context.projection

        ra_interval, _ = self._get_grid_interval(context.scene.sky_camera.fov_deg)
        for ra, line in projection.iter_ra_lines(
            projection_context,
            viewport.size(),
            ra_interval
        ):
            self._set_pen(painter, scene.rendering_settings.color_settings.ra_dec_grid_color)
            painter.setBrush(scene.rendering_settings.color_settings.ra_dec_grid_color)
            self._draw_polyline(context, line)
            self._draw_ra_grid_label(context, Position(ra, projection.visible_bounds(projection_context, viewport.size())[0].dec_deg))


    def _draw_dec_grid(self, context: RendererContext[Position, LinearProjection]) -> None:
        painter = context.painter
        scene = context.scene
        viewport = context.viewport
        projection_context = context.projection_context
        projection = context.projection

        _, dec_interval = self._get_grid_interval(context.scene.sky_camera.fov_deg)
        for dec, line in projection.iter_dec_lines(
            projection_context,
            viewport.size(),
            dec_interval
        ):
            self._set_pen(painter, scene.rendering_settings.color_settings.ra_dec_grid_color)
            painter.setBrush(scene.rendering_settings.color_settings.ra_dec_grid_color)
            self._draw_polyline(context, line)
            self._draw_dec_grid_label(context, Position(projection.visible_bounds(projection_context, viewport.size())[0].ra_deg, dec))

    def _draw_polyline(self, context: RendererContext[Position, LinearProjection], positions: Iterable[Position]) -> None:
        previous = None
        for pos in positions:
            point = context.projection.project(pos, context.projection_context, context.viewport.size())
            if point is None:
                previous = None
                continue

            if previous is not None:
                context.painter.drawLine(previous, point)

            previous = point

    def _iter_ra_line(self, ra: float, min_dec: float, max_dec: float, dec_interval: float) -> Iterable[Position]:
        dec = min_dec
        while dec <= max_dec:
            yield Position(ra, dec)
            dec += dec_interval

    def _iter_dec_line(self, dec: float, min_ra: float, max_ra: float, ra_interval: float) -> Iterable[Position]:
        ra = min_ra
        while ra < max_ra:
            yield Position(ra % 360, dec)
            ra += ra_interval


    def _draw_ra_grid_label(self, context: RendererContext[Position, LinearProjection], position: Position) -> None:
        painter = context.painter
        scene = context.scene

        point = context.projection.project(position, context.projection_context, context.viewport.size())
        if point is None:
            return

        if scene.rendering_settings.ra_format == RightAscensionFormat.HMS:
            label = format_ra_hms(position.ra_deg, False)
        else:
            label = format_ra_deg(position.ra_deg)

        self._set_pen(painter, scene.rendering_settings.color_settings.ra_dec_label_color)
        painter.drawText(point + QPoint(5, -5), label)


    def _draw_dec_grid_label(self, context: RendererContext[Position, LinearProjection], position: Position) -> None:
        painter = context.painter
        scene = context.scene

        point = context.projection.project(position, context.projection_context, context.viewport.size())
        if point is None:
            return

        label = format_dec_deg(position.dec_deg)
        self._set_pen(painter, scene.rendering_settings.color_settings.ra_dec_label_color)
        painter.drawText(point + QPoint(5, -5), label)


    # TODO: 以下実装
    # def _draw_celestial_equator(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
    #     raise NotImplementedError("Celestial equator drawing is not implemented yet.")

    # def _draw_ecliptic(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
    #     raise NotImplementedError("Ecliptic drawing is not implemented yet.")


    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)