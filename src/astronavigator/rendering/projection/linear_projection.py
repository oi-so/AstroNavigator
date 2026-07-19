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