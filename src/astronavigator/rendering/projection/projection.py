from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator, Generic, Iterable, TypeVar

from PySide6.QtCore import QPoint, QPointF, QSize

from astronavigator.scene.scene import Scene
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.sky.position import HorizontalPosition, Position
from astronavigator.sky.sky_object import SkyObject



T = TypeVar("T")
C = TypeVar("C")
GridPosition = Position | HorizontalPosition


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


    @abstractmethod
    def iter_grid_lines(self, context: C, viewport_size: QSize, interval: float) -> Generator[tuple[float, Iterable[T]], None, None]:
        """
        ビューポート内に表示されるグリッド線を反復する。
        Iterate over grid lines visible within the viewport.

        Parameters
        ----------
        context : C
            投影コンテキスト。
        viewport_size : QSize
            ビューポートのサイズ。
        interval : float
            グリッド線の間隔（度単位）。
        """


    @abstractmethod
    def project_object(self, obj: SkyObject, context: C, viewport_size: QSize) -> QPointF | None:
        """
        オブジェクトをスクリーン座標に投影する。
        Project an object to screen coordinates.

        Parameters
        ----------
        obj : SkyObject
            投影するオブジェクト。The object to project.
        context : C
            投影コンテキスト。Projection context.
        viewport_size : QSize
            ビューポートのサイズ。Viewport size.

        Returns
        -------
        QPointF | None
            スクリーン座標。Screen coordinates.
            Noneの場合、オブジェクトはビューポート内に表示されない。If None, the object is not visible within the viewport.
        """

    @abstractmethod
    def project_grid_position(
        self,
        position: GridPosition,
        coordinate_system: CoordinateSystem,
        context: C,
        viewport_size: QSize
    ) -> QPointF | None:
        """
        グリッド座標を現在の投影方式でスクリーン座標に投影する。
        Project a grid coordinate in its native coordinate system.
        """


    @abstractmethod
    def convert_position(self, position: Position, context: C) -> T:
        """
        天球上の座標を投影コンテキストに基づいて変換する。
        Convert celestial coordinates based on the projection context.

        Parameters
        ----------
        position : T
            変換する天球上の座標。The celestial coordinates to convert.
        context : C
            投影コンテキスト。Projection context.

        Returns
        -------
        T
            変換後の天球上の座標。The converted celestial coordinates.
        """



    def project_many(self, positions, context: C, viewport_size: QSize) -> list[QPointF | None]:
        """
        複数の天球上の座標をスクリーン座標に投影する。
        Project multiple celestial coordinates to screen coordinates.

        Parameters
        ----------
        positions : Iterable[T]
            投影する天球上の座標のイテラブル。An iterable of celestial coordinates to project.
        context : C
            投影コンテキスト。Projection context.
        viewport_size : QSize
            ビューポートのサイズ。Viewport size.

        Returns
        -------
        list[QPointF | None]
            スクリーン座標のリスト。A list of screen coordinates.
            Noneの場合、対応する天球上の座標はビューポート内に表示されない。If None, the corresponding celestial coordinate is not visible within the viewport.
        """
        return [self.project(position, context, viewport_size) for position in positions]


    @abstractmethod
    def calculate_dragged_center(self, previous_position: QPoint, current_position: QPoint, context: C, viewport_size: QSize) -> Position:
        """
        ドラッグ操作によって移動した中心座標を計算する。
        Calculate the new center coordinates after a drag operation.

        Parameters
        ----------
        previous_position : QPointF
            ドラッグ開始時のスクリーン座標。Screen coordinates at the start of the drag.
        current_position : QPointF
            ドラッグ終了時のスクリーン座標。Screen coordinates at the end of the drag.
        context : C
            投影コンテキスト。Projection context.
        viewport_size : QSize
            ビューポートのサイズ。Viewport size.

        Returns
        -------
        Position
            ドラッグ操作によって移動した中心座標。The new center coordinates after the drag operation.
        """


    @abstractmethod
    def get_center_horizontal_position(self, context: C) -> HorizontalPosition:
        """
        現在の投影コンテキストに基づいて、中心の水平座標を取得する。
        Get the current center horizontal coordinates based on the projection context.

        Parameters
        ----------
        context : C
            投影コンテキスト。Projection context.

        Returns
        -------
        HorizontalPosition
            中心の水平座標。The current center horizontal coordinates.
        """