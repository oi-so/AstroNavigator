from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar, Iterable
from abc import ABC, abstractmethod
import math

from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext

T = TypeVar("T")


GRID_SAMPLES_PER_INTERVAL = 4.0
GRID_SAMPLE_FOV_DIVISOR = 18.0

MIN_GRID_SAMPLE_INTERVAL_DEG = 1.0
MAX_GRID_SAMPLE_INTERVAL_DEG = 10.0

MIN_LATITUDE_COSINE = 0.15
MAX_LONGITUDE_SAMPLE_INTERVAL_DEG = 20.0
MAX_PARALLEL_SAMPLES = 120

MAX_LONGITUDE_GRID_LINES = 12
NICE_LONGITUDE_INTERVALS_DEG = (
    0.1,
    0.2,
    0.5,
    1.0,
    2.0,
    3.0,
    5.0,
    6.0,
    9.0,
    10.0,
    15.0,
    18.0,
    30.0,
    45.0,
    90.0,
)


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


def calculate_grid_sample_interval(interval: float, fov_deg: float) -> float:
    fov_sample_interval = fov_deg / GRID_SAMPLE_FOV_DIVISOR
    fov_sample_interval = max(
        MIN_GRID_SAMPLE_INTERVAL_DEG, 
        min(fov_sample_interval, MAX_GRID_SAMPLE_INTERVAL_DEG)
    )

    return min(interval / GRID_SAMPLES_PER_INTERVAL, fov_sample_interval)


def calculate_parallel_sample_interval(interval: float, latitude: float, longitude_span: float) -> float:
    latitude_cosine = abs(math.cos(math.radians(latitude)))
    latitude_cosine = max(MIN_LATITUDE_COSINE, latitude_cosine)

    latitude_interval = interval / latitude_cosine
    budget_interval = longitude_span / MAX_PARALLEL_SAMPLES
    return min(
        MAX_LONGITUDE_SAMPLE_INTERVAL_DEG,
        max(interval, latitude_interval, budget_interval)
    )


def format_grid_degree(value: float, interval: float, *, signed: bool = False) -> str:
    decimal_places = 1 if interval < 1.0 else 0
    if signed:
        return f"{value:+.{decimal_places}f}°"
    else:
        return f"{value:.{decimal_places}f}°"


def calculate_spherical_longitude_bounds(center_longitude_deg: float, center_latitude_deg: float, half_fov_deg: float) -> tuple[float, float]:
    raw_min_latitude = center_latitude_deg - half_fov_deg
    raw_max_latitude = center_latitude_deg + half_fov_deg

    if raw_min_latitude <= -90.0 or raw_max_latitude >= 90.0:
        return (0.0, 360.0)

    latitude_rad = math.radians(center_latitude_deg)
    half_fov_rad = math.radians(half_fov_deg)

    longitude_ratio = math.sin(half_fov_rad) / max(abs(math.cos(latitude_rad)), 1e-12)
    half_longitude_deg = math.degrees(math.asin(longitude_ratio))

    return (center_longitude_deg - half_longitude_deg, center_longitude_deg + half_longitude_deg)


def calculate_longitude_grid_interval(base_interval: float, longitude_span: float) -> float:
    if longitude_span <= 0.0:
        return base_interval

    required_interval = max(base_interval, longitude_span / MAX_LONGITUDE_GRID_LINES)
    for interval in NICE_LONGITUDE_INTERVALS_DEG:
        if interval + 1e-9 >= required_interval:
            return interval
    return NICE_LONGITUDE_INTERVALS_DEG[-1]


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