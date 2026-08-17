from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar, Iterable
from abc import ABC, abstractmethod

from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext

T = TypeVar("T")


GRID_SAMPLES_PER_INTERVAL = 4.0

MEDIUM_SAMPLE_FOV_DEG = 60.0
WIDE_SAMPLE_FOV_DEG = 120.0

NARROW_MAX_SAMPLE_INTERVAL = 1.0
MEDIUM_MAX_SAMPLE_INTERVAL = 3.0
WIDE_MAX_SAMPLE_INTERVAL = 10.0


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


def calculate_grid_sample_interval(grid_interval: float, fov_deg: float) -> float:
    if fov_deg >= WIDE_SAMPLE_FOV_DEG:
        max_sample_interval = WIDE_MAX_SAMPLE_INTERVAL
    elif fov_deg >= MEDIUM_SAMPLE_FOV_DEG:
        max_sample_interval = MEDIUM_MAX_SAMPLE_INTERVAL
    else:
        max_sample_interval = NARROW_MAX_SAMPLE_INTERVAL

    return min(grid_interval / GRID_SAMPLES_PER_INTERVAL, max_sample_interval)


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