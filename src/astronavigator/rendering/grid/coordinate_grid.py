from __future__ import annotations

from typing import Generic, TypeVar, Iterable
from abc import ABC, abstractmethod

from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.render_context import RendererContext

T = TypeVar("T")



class CoordinateGrid(ABC, Generic[T]):
    @abstractmethod
    def iter_lines(self, context: RendererContext) -> Iterable[Iterable[T]]:
        ...

    @property
    @abstractmethod
    def coordinate_system(self) -> CoordinateSystem:
        ...