from __future__ import annotations
from collections.abc import Iterable
from typing import TypeVar


from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.grid.horizontal_grid import HorizontalGrid
from astronavigator.rendering.grid.equatorial_gird import EquatorialGrid
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.grid.grid_manager import GridManager
from astronavigator.rendering.render_context import RendererContext


T = TypeVar("T")

class GridLayer(Layer):
    def __init__(self) -> None:
        super().__init__(visible=True, layer_type=LayerType.GRID)

        self.grid_manager = GridManager()
        self.grid_manager.add_grid(EquatorialGrid())
        self.grid_manager.add_grid(HorizontalGrid())

    # @profile
    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return

        for grid in self.grid_manager.grids():
            if not context.scene.rendering_settings.grid_settings.is_visible.get(grid.coordinate_system, False):
                continue

            color = context.scene.rendering_settings.grid_settings.colors.get(grid.coordinate_system)
            context.painter.setPen(color)

            for line in grid.iter_lines(context):
                self._draw_line(context, grid.coordinate_system, line)


    def _draw_line(self, context: RendererContext, coordinate_system: CoordinateSystem, positions: Iterable[T]) -> None:
        previous = None

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

            previous = point
