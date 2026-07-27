from __future__ import annotations

from bisect import bisect_right
from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter
from collections import OrderedDict

from astronavigator.scene.scene import Scene
from astronavigator.sky.position import Position


GRID_INTERVAL_TABLE: OrderedDict[float, tuple[float, float]] = OrderedDict({
    0: (0.1, 0.1),
    0.1: (0.2, 0.2),
    0.3: (0.5, 0.5),
    1: (1, 1),
    3: (2, 2),
    10: (5, 5),
    30: (10, 10),
    90: (15, 15),
    180: (30, 30),
})

SORTED_GRID_INTERVAL_KEYS = sorted(GRID_INTERVAL_TABLE.keys())




class GridRenderer:
    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        camera_fov = scene.sky_camera.fov_deg
        self._draw_ra_grid(painter, scene, viewport, camera_fov)
        self._draw_dec_grid(painter, scene, viewport, camera_fov)
        # self._draw_celestial_equator(painter, scene, viewport)
        # self._draw_ecliptic(painter, scene, viewport)

    
    def _get_grid_interval(self, camera_fov: float) -> tuple[float, float]:
        index = bisect_right(SORTED_GRID_INTERVAL_KEYS, camera_fov)
        if index == 0:
            raise ValueError("Camera FOV is too small for grid rendering.")
        
        return GRID_INTERVAL_TABLE[SORTED_GRID_INTERVAL_KEYS[index - 1]]


    def _draw_ra_grid(self, painter: QPainter, scene: Scene, viewport: QRect, camera_fov: float) -> None:
        ra_interval, dec_interval = self._get_grid_interval(camera_fov)
        ra = 0
        dec = -90
        while dec <= 90:
            previous = None
            while ra < 360:
                point = scene.sky_camera.project(Position(ra, dec), viewport.size())
                if point is None:
                    previous = None
                    ra += ra_interval
                    continue

                if previous is not None:
                    painter.drawLine(previous, point)

                previous = point
                ra += ra_interval

            dec += dec_interval
            ra = 0


    def _draw_dec_grid(self, painter: QPainter, scene: Scene, viewport: QRect, camera_fov: float) -> None:
        ra_interval, dec_interval = self._get_grid_interval(camera_fov)

        ra = 0
        dec = -90
        while ra < 360:
            previous = None
            while dec <= 90:
                point = scene.sky_camera.project(Position(ra, dec), viewport.size())
                if point is None:
                    previous = None
                    dec += dec_interval
                    continue

                if previous is not None:
                    painter.drawLine(previous, point)

                previous = point
                dec += dec_interval

            ra += ra_interval
            dec = -90

    # def _draw_celestial_equator(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
    #     raise NotImplementedError("Celestial equator drawing is not implemented yet.")

    # def _draw_ecliptic(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
    #     raise NotImplementedError("Ecliptic drawing is not implemented yet.")