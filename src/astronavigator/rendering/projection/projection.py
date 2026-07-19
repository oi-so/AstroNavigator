from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QSize

from astronavigator.sky.position import Position

if TYPE_CHECKING:
    from astronavigator.camera.sky_camera import SkyCamera


class Projection(ABC):
    @abstractmethod
    def project(
        self, 
        position: Position, 
        camera: SkyCamera, 
        viewport_size: QSize
    ) -> QPointF | None:
        ...

    @abstractmethod
    def unproject(
        self, 
        screen_position: QPointF, 
        camera: SkyCamera, 
        viewport_size: QSize
    ) -> Position:
        """
        スクリーン座標を天球上の座標へ変換する。
        Convert screen coordinates to celestial coordinates.

        Parameters
        ----------
        screen_position : QPointF
            スクリーン座標。Screen coordinates.
        camera : SkyCamera
            スカイカメラ。
        viewport_size : QSize
            ビューポートのサイズ。

        Returns
        -------
        Position
            Position: 天球上の座標。Celestial coordinates.
        """