from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QSize

from astronavigator.rendering.projection.projection import Projection
from astronavigator.sky.position import Position

if TYPE_CHECKING:
    from astronavigator.camera.sky_camera import SkyCamera


class LinearProjection(Projection):
    def project(
        self, 
        position: Position, 
        camera: SkyCamera, 
        viewport_size: QSize
    ) -> QPointF | None:
        delta_ra = position.ra_deg - camera.center.ra_deg
        delta_ra = ((delta_ra + 180) % 360) - 180
        delta_dec = position.dec_deg - camera.center.dec_deg

        width = viewport_size.width()
        height = viewport_size.height()

        scale = min(width, height) / camera.fov_deg

        x = width / 2 + delta_ra * scale
        y = height / 2 - delta_dec * scale

        if x < 0 or x > width or y < 0 or y > height:
            return None
        
        # TODO: Apply camera rotation
        
        return QPointF(x, y)


    def unproject(
        self, 
        screen_position: QPointF, 
        camera: SkyCamera, 
        viewport_size: QSize
    ) -> Position:
        raise NotImplementedError("Orthographic unprojection is not implemented yet.")


    def visible_bounds(self, camera: SkyCamera, viewport_size: QSize) -> tuple[Position, Position]:
        width = viewport_size.width()
        height = viewport_size.height()

        scale = min(width, height) / camera.fov_deg

        half_width_deg = (width / 2) / scale
        half_height_deg = (height / 2) / scale

        min_ra = camera.center.ra_deg - half_width_deg
        max_ra = camera.center.ra_deg + half_width_deg
        min_dec = camera.center.dec_deg - half_height_deg
        max_dec = camera.center.dec_deg + half_height_deg

        return Position(min_ra, min_dec), Position(max_ra, max_dec)