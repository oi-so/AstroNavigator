from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING
from PySide6.QtCore import QPointF, QSize

from astronavigator.rendering.projection.linear_projection import LinearProjection
from astronavigator.sky.position import Position

if TYPE_CHECKING:
    from astronavigator.rendering.projection.projection import Projection


@dataclass(slots=True)
class SkyCamera:
    center: Position
    fov_deg: float
    rotation: float
    projection: Projection 
    limit_magnitude: float = 6.0  # Default limit magnitude for visibility


    @classmethod
    def default(cls) -> "SkyCamera":
        return SkyCamera(
            center=Position(0, 0),
            fov_deg=90,
            rotation=0,
            projection=LinearProjection()
        )
    
    def move(self, delta_ra: float, delta_dec: float):
        self.center = self.center.moved(delta_ra, delta_dec)

    def zoom(self, factor: float):
        self.fov_deg *= factor
        self.fov_deg = max(5.0, min(180.0, self.fov_deg))  # Clamp FOV between 5 and 180 degrees


    def project(self, position: Position, viewport_size: QSize) -> QPointF | None:
        """"
        天球上の座標をスクリーン座標へ変換する。
        Convert celestial coordinates to screen coordinates.

        Parameters
        ----------
        position : Position
            天球上の座標。Celestial coordinates.
        camera : SkyCamera
            スカイカメラ。
        viewport_size : QSize
            ビューポートのサイズ。

        Returns
        -------
        QPointF | None
            QPointF: スクリーン座標。Screen coordinates.
            None: 表示範囲外。Out of display range.
        """
        return self.projection.project(position, self, viewport_size)


    def visible_ra_range(self, viewport_size: QSize) -> tuple[float, float]:
        return self.projection.visible_bounds(self, viewport_size)[0].ra_deg, self.projection.visible_bounds(self, viewport_size)[1].ra_deg


    def visible_dec_range(self, viewport_size: QSize) -> tuple[float, float]:
        return self.projection.visible_bounds(self, viewport_size)[0].dec_deg, self.projection.visible_bounds(self, viewport_size)[1].dec_deg