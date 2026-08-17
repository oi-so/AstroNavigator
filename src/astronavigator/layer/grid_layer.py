from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, auto
import math
from typing import TypeVar
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainterPath

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.grid.coordinate_grid import GridLabelPlacement
from astronavigator.rendering.grid.horizontal_grid import HorizontalGrid
from astronavigator.rendering.grid.equatorial_gird import EquatorialGrid
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.grid.grid_manager import GridManager
from astronavigator.rendering.render_context import RendererContext


T = TypeVar("T")

GRID_LABEL_MINIMUM_ALPHA = 200

POINT_LABEL_VISIBILITY_TOLERANCE = 1.0
POINT_LABEL_DIRECTION_EPSILON = 1e-9


class GridLabelEdge(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()

@dataclass(frozen=True, slots=True)
class GridLabel:
    text: str
    color: QColor
    anchor: QPointF
    edge: GridLabelEdge | None = None
    offset_direction: QPointF | None = None

class GridLayer(Layer):
    def __init__(self) -> None:
        super().__init__(visible=True, layer_type=LayerType.GRID)

        self.grid_manager = GridManager()
        self.grid_manager.add_grid(EquatorialGrid())
        self.grid_manager.add_grid(HorizontalGrid())

        self._labels: list[GridLabel] = []

    @property
    def labels(self) -> tuple[GridLabel, ...]:
        return tuple(self._labels)

    # @profile
    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return

        self._labels.clear()
        grid_settings = context.scene.rendering_settings.grid_settings

        painter = context.painter
        painter.save()

        try:
            clip_path = context.projection.create_clip_path(
                context.projection_context,
                context.viewport.size()
            )
            painter.setClipPath(clip_path, Qt.ClipOperation.IntersectClip)

            for grid in self.grid_manager.grids():
                if not grid_settings.is_visible.get(grid.coordinate_system, False):
                    continue

                color = grid_settings.colors.get(grid.coordinate_system)
                if color is None:
                    continue

                painter.setPen(color)

                for line in grid.iter_lines(context):
                    label_anchor = self._draw_line(context, grid.coordinate_system, line.positions, line.label_placement, clip_path)
                    if label_anchor is None:
                        continue

                    anchor, edge = label_anchor

                    label_color = QColor(color)
                    label_color.setAlpha(max(label_color.alpha(), GRID_LABEL_MINIMUM_ALPHA))
                    self._labels.append(GridLabel(text=line.label, color=label_color, anchor=anchor, edge=edge))

                for point_label in grid.iter_point_labels(context):
                    anchor = context.projection.project_grid_position_unclipped(
                        point_label.position, grid.coordinate_system, context.projection_context, context.viewport.size()
                    )
                    toward_point = context.projection.project_grid_position_unclipped(
                        point_label.offset_position,
                        grid.coordinate_system,
                        context.projection_context,
                        context.viewport.size(),
                    )

                    if anchor is None or toward_point is None:
                        continue

                    anchor_area = QRectF(
                        anchor.x() - POINT_LABEL_VISIBILITY_TOLERANCE,
                        anchor.y() - POINT_LABEL_VISIBILITY_TOLERANCE,
                        2.0 * POINT_LABEL_VISIBILITY_TOLERANCE,
                        2.0 * POINT_LABEL_VISIBILITY_TOLERANCE
                    )

                    if not clip_path.contains(anchor) and not clip_path.intersects(anchor_area):
                        continue

                    if not clip_path.contains(toward_point):
                        continue

                    dx = toward_point.x() - anchor.x()
                    dy = toward_point.y() - anchor.y()
                    direction_length = math.hypot(dx, dy)

                    if direction_length <= POINT_LABEL_DIRECTION_EPSILON:
                        continue

                    direction = QPointF(dx / direction_length, dy / direction_length)

                    point_label_color = QColor(color)
                    point_label_color.setAlpha(max(point_label_color.alpha(), GRID_LABEL_MINIMUM_ALPHA))
                    self._labels.append(GridLabel(text=point_label.text, color=point_label_color, anchor=anchor, offset_direction=direction))
        finally:
            painter.restore()

    # @profile
    def _draw_line(self, context: RendererContext, coordinate_system: CoordinateSystem, positions: Iterable[T], label_placement: GridLabelPlacement, clip_path: QPainterPath) -> tuple[QPointF, GridLabelEdge] | None:
        previous_line_point: QPointF | None = None
        previous_is_visible = False

        candidates: list[tuple[QPointF, GridLabelEdge]] = []

        topmost_point: QPointF | None = None
        leftmost_point: QPointF | None = None

        viewport_size = context.viewport.size()
        width = float(viewport_size.width())
        height = float(viewport_size.height())

        for position in positions:
            line_point = context.projection.project_grid_position_unclipped(
                position, coordinate_system, context.projection_context, viewport_size
            )

            if line_point is None:
                previous_line_point = None
                previous_is_visible = False
                continue

            inside = clip_path.contains(line_point)

            if inside:
                if topmost_point is None or line_point.y() < topmost_point.y():
                    topmost_point = line_point
                if leftmost_point is None or line_point.x() < leftmost_point.x():
                    leftmost_point = line_point

            if previous_line_point is not None:
                if previous_is_visible or inside:
                    context.painter.drawLine(previous_line_point, line_point)

                if previous_is_visible != inside:
                    intersection_point = self._find_clip_intersection(previous_line_point, line_point, previous_is_visible, clip_path)
                    edge = self._classify_edge(intersection_point, width, height)

                    if self._edge_matches_placement(edge, label_placement):
                        candidates.append((intersection_point, edge))

            previous_line_point = line_point
            previous_is_visible = inside

        preferred_edge = (
            (GridLabelEdge.TOP, GridLabelEdge.BOTTOM) 
            if label_placement == GridLabelPlacement.TOP_BOTTOM
            else (GridLabelEdge.LEFT, GridLabelEdge.RIGHT)
        )


        for preferred_edge in preferred_edge:
            edge_candidates = [c for c in candidates if c[1] == preferred_edge]
            if edge_candidates:
                return edge_candidates[0]

        if label_placement == GridLabelPlacement.TOP_BOTTOM:
            if topmost_point is not None:
                return (topmost_point, GridLabelEdge.TOP)
        else:
            if leftmost_point is not None:
                return (leftmost_point, GridLabelEdge.LEFT)

        return None


    @staticmethod
    def _find_clip_intersection(p1: QPointF, p2: QPointF, p1_inside: bool, clip_path: QPainterPath) -> QPointF:
        inside_point = p1 if p1_inside else p2
        outside_point = p2 if p1_inside else p1

        for _ in range(10):
            middle = QPointF(
                (inside_point.x() + outside_point.x()) / 2, 
                (inside_point.y() + outside_point.y()) / 2
            )

            if clip_path.contains(middle):
                inside_point = middle
            else:
                outside_point = middle
        return inside_point

    @staticmethod
    def _classify_edge(point: QPointF, width: float, height: float) -> GridLabelEdge:
        distances = (
            (abs(point.x()), GridLabelEdge.LEFT),
            (abs(point.x() - width), GridLabelEdge.RIGHT),
            (abs(point.y()), GridLabelEdge.TOP),
            (abs(point.y() - height), GridLabelEdge.BOTTOM)
        )
        return min(distances, key=lambda x: x[0])[1]

    @staticmethod
    def _edge_matches_placement(edge: GridLabelEdge, placement: GridLabelPlacement) -> bool:
        if placement == GridLabelPlacement.TOP_BOTTOM:
            return edge in (GridLabelEdge.TOP, GridLabelEdge.BOTTOM)
        else:
            return edge in (GridLabelEdge.LEFT, GridLabelEdge.RIGHT)