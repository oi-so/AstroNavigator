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


    @classmethod
    def default(cls) -> "SkyCamera":
        return SkyCamera(
            center=Position(0, 0),
            fov_deg=90,
            rotation=0,
            projection=LinearProjection()
        )
    

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