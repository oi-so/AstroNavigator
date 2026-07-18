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