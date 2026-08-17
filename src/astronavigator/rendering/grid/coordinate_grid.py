from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar, Iterable
from abc import ABC, abstractmethod

from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext

T = TypeVar("T")


GRID_SAMPLES_PER_INTERVAL = 4.0
MAX_GRID_SAMPLE_INTERVAL_DEG = 1.0


class GridLabelPlacement(Enum):
    TOP_BOTTOM = auto()
    LEFT_RIGHT = auto()


@dataclass(slots=True)
class GridLine(Generic[T]):
    positions: Iterable[T]
    label: str
    label_placement: GridLabelPlacement

@dataclass(slots=True)
class GridPointLabel(Generic[T]):
    position: T
    offset_position: T
    text: str


def calculate_grid_sample_interval(grid_interval: float) -> float:
    return min(grid_interval / GRID_SAMPLES_PER_INTERVAL, MAX_GRID_SAMPLE_INTERVAL_DEG)


def format_grid_degree(value: float, interval: float, *, signed: bool = False) -> str:
    decimal_places = 1 if interval < 1.0 else 0
    if signed:
        return f"{value:+.{decimal_places}f}°"
    else:
        return f"{value:.{decimal_places}f}°"


class CoordinateGrid(ABC, Generic[T]):
    @abstractmethod
    def iter_lines(self, context: RendererContext) -> Iterable[GridLine[T]]:
        ...


    def iter_point_labels(self, context: RendererContext) -> Iterable[GridPointLabel[T]]:
        return ()

    @property
    @abstractmethod
    def coordinate_system(self) -> CoordinateSystem:
        ...