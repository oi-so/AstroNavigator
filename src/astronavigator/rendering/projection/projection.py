from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from PySide6.QtCore import QPointF, QSize

from astronavigator.scene.scene import Scene



T = TypeVar("T")
C = TypeVar("C")


class Projection(ABC, Generic[T, C]):
    @abstractmethod
    def project(
        self, 
        position: T, 
        context: C, 
        viewport_size: QSize
    ) -> QPointF | None:
        ...

    @abstractmethod
    def unproject(
        self, 
        screen_position: QPointF, 
        context: C, 
        viewport_size: QSize
    ) -> T:
        """
        スクリーン座標を天球上の座標へ変換する。
        Convert screen coordinates to celestial coordinates.

        Parameters
        ----------
        screen_position : QPointF
            スクリーン座標。Screen coordinates.
        context : C
            投影コンテキスト。
        viewport_size : QSize
            ビューポートのサイズ。

        Returns
        -------
        T
            T: 天球上の座標。Celestial coordinates.
        """

    @abstractmethod
    def visible_bounds(self, context: C, viewport_size: QSize) -> tuple[T, T]:
        """
        ビューポート内に表示される天球上の範囲を取得する。
        Get the range of celestial coordinates visible within the viewport.

        Parameters
        ----------
        context : C
            投影コンテキスト。
        viewport_size : QSize
            ビューポートのサイズ。

        Returns
        -------
        tuple[T, T]
            T: ビューポート内に表示される天球上の範囲の最小座標。Minimum celestial coordinates visible within the viewport.
            T: ビューポート内に表示される天球上の範囲の最大座標。Maximum celestial coordinates visible within the viewport.
        """


    @abstractmethod
    def create_context(self, scene: Scene) -> C:
        """
        投影コンテキストを作成する。
        Create a projection context.

        Parameters
        ----------
        scene : Scene
            シーン。Scene.

        Returns
        -------
        C
            投影コンテキスト。Projection context.
        """

    # @abstractmethod
    # def iter_ra_lines(self, context: C, viewport_size: QSize, interval_deg: float) -> Generator[tuple[float, Iterable[T]], None, None]:
    #     ...

    # @abstractmethod
    # def iter_dec_lines(self, context: C, viewport_size: QSize, interval_deg: float) -> Generator[tuple[float, Iterable[T]], None, None]:
    #     ...