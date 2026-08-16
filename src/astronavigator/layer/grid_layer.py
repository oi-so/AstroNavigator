from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeVar
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.grid.horizontal_grid import HorizontalGrid
from astronavigator.rendering.grid.equatorial_gird import EquatorialGrid
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.grid.grid_manager import GridManager
from astronavigator.rendering.render_context import RendererContext


T = TypeVar("T")

GRID_LABEL_MINIMUM_ALPHA = 200

@dataclass(frozen=True, slots=True)
class GridLabel:
    text: str
    color: QColor
    anchor: QPointF

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
                    anchor = self._draw_line(context, grid.coordinate_system, line.positions)
                    if anchor is None:
                        continue

                    label_color = QColor(color)
                    label_color.setAlpha(max(label_color.alpha(), GRID_LABEL_MINIMUM_ALPHA))
                    self._labels.append(GridLabel(text=line.label, color=label_color, anchor=anchor))
        finally:
            painter.restore()

    # @profile
    def _draw_line(self, context: RendererContext, coordinate_system: CoordinateSystem, positions: Iterable[T]) -> QPointF | None:
        previous_line_point: QPointF | None = None
        previous_is_visible = False

        closest_point: QPointF | None = None
        closest_edge_distance = float("inf")

        viewport_size = context.viewport.size()
        width = float(viewport_size.width())
        height = float(viewport_size.height())

        for position in positions:
            visible_point = context.projection.project_grid_position(
                position, coordinate_system, context.projection_context, viewport_size
            )

            line_point = context.projection.project_grid_position_unclipped(
                position, coordinate_system, context.projection_context, viewport_size
            )

            if line_point is None:
                previous_line_point = None
                previous_is_visible = False
                continue

            is_visible = visible_point is not None

            if previous_line_point is not None and (previous_is_visible or is_visible):
                context.painter.drawLine(previous_line_point, line_point)

            if visible_point is not None:
                edge_distance = min(
                    visible_point.x(), 
                    width - visible_point.x(), 
                    visible_point.y(), 
                    height - visible_point.y()
                    )
                
                if edge_distance < closest_edge_distance:
                    closest_edge_distance = edge_distance
                    closest_point = visible_point

            previous_line_point = line_point
            previous_is_visible = is_visible

        return closest_point
