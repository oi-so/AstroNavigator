from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeVar
from PySide6.QtCore import QPointF
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

        for grid in self.grid_manager.grids():
            if not context.scene.rendering_settings.grid_settings.is_visible.get(grid.coordinate_system, False):
                continue

            color = context.scene.rendering_settings.grid_settings.colors.get(grid.coordinate_system)
            context.painter.setPen(color)

            for line in grid.iter_lines(context):
                anchor = self._draw_line(context, grid.coordinate_system, line.positions)

                if anchor is None:
                    continue

                label_color = QColor(color)
                label_color.setAlpha(max(label_color.alpha(), GRID_LABEL_MINIMUM_ALPHA))
                self._labels.append(GridLabel(text=line.label, color=label_color, anchor=anchor))

    # @profile
    def _draw_line(self, context: RendererContext, coordinate_system: CoordinateSystem, positions: Iterable[T]) -> QPointF | None:
        previous: QPointF | None = None
        closest_point: QPointF | None = None
        closest_edge_distance = float("inf")

        viewport_size = context.viewport.size()
        width = float(viewport_size.width())
        height = float(viewport_size.height())

        for position in positions:
            point = context.projection.project_grid_position(
                position,
                coordinate_system,
                context.projection_context,
                context.viewport.size()
            )

            if point is None:
                previous = None
                continue

            if previous is not None:
                context.painter.drawLine(previous, point)

            edge_distance = min(point.x(), width - point.x(), point.y(), height - point.y())
            if edge_distance < closest_edge_distance:
                closest_edge_distance = edge_distance
                closest_point = point

            previous = point

        return closest_point
