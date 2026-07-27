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
        """"
        現在のカメラの視野における赤経の範囲を取得する。
        Get the range of right ascension in the current camera's field of view.

        Returns
        -------
        tuple[float, float]
            赤経の範囲 (min_ra, max_ra)。
            Range of right ascension (min_ra, max_ra).
        """
        width = viewport_size.width()
        height = viewport_size.height()
        scale = min(width, height) / self.fov_deg
        half_ra = (width / 2) / scale
        min_ra = self.center.ra_deg - half_ra
        max_ra = self.center.ra_deg + half_ra
        return min_ra, max_ra


    def visible_dec_range(self, viewport_size: QSize) -> tuple[float, float]:
        """"
        現在のカメラの視野における赤緯の範囲を取得する。
        Get the range of declination in the current camera's field of view.

        Returns
        -------
        tuple[float, float]
            赤緯の範囲 (min_dec, max_dec)。
            Range of declination (min_dec, max_dec).
        """
        width = viewport_size.width()
        height = viewport_size.height()
        scale = min(width, height) / self.fov_deg
        half_dec = (height / 2) / scale
        min_dec = max(-90, self.center.dec_deg - half_dec)
        max_dec = min(90, self.center.dec_deg + half_dec)
        return min_dec, max_dec