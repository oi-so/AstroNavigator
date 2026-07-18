from __future__ import annotations

from PySide6.QtCore import QPointF, QSize

from astronavigator.camera.sky_camera import SkyCamera
from astronavigator.rendering.projection.projection import Projection
from astronavigator.sky.position import Position


class OrthographicProjection(Projection):
    def project(
        self, 
        position: Position, 
        camera: SkyCamera, 
        viewport_size: QSize
    ) -> QPointF | None:
        if position == camera.center:
            return QPointF(viewport_size.width() / 2, viewport_size.height() / 2)
        else:
            raise NotImplementedError("Orthographic projection is not implemented yet.")
    
    def unproject(
        self, 
        screen_position: QPointF, 
        camera: SkyCamera, 
        viewport_size: QSize
    ) -> Position:
        raise NotImplementedError("Orthographic unprojection is not implemented yet.")