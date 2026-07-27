from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable

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

    @abstractmethod
    def visible_bounds(self, camera: SkyCamera, viewport_size: QSize) -> tuple[Position, Position]:
        """
        ビューポート内に表示される天球上の範囲を取得する。
        Get the range of celestial coordinates visible within the viewport.

        Parameters
        ----------
        camera : SkyCamera
            スカイカメラ。
        viewport_size : QSize
            ビューポートのサイズ。

        Returns
        -------
        tuple[Position, Position]
            Position: ビューポート内に表示される天球上の範囲の最小座標。Minimum celestial coordinates visible within the viewport.
            Position: ビューポート内に表示される天球上の範囲の最大座標。Maximum celestial coordinates visible within the viewport.
        """

    @abstractmethod
    def iter_ra_lines(self, camera: SkyCamera, viewport_size: QSize, interval_deg: float) -> Iterable[Iterable[Position]]:
        ...

    @abstractmethod
    def iter_dec_lines(self, camera: SkyCamera, viewport_size: QSize, interval_deg: float) -> Iterable[Iterable[Position]]:
        ...