from __future__ import annotations

from astronavigator.rendering.grid.coordinate_grid import CoordinateGrid


class GridManager:
    def __init__(self) -> None:
        self._grids = []

    def add_grid(self, grid: CoordinateGrid) -> None:
        self._grids.append(grid)

    def remove_grid(self, grid: CoordinateGrid) -> None:
        self._grids.remove(grid)

    def grids(self) -> list[CoordinateGrid]:
        return self._grids