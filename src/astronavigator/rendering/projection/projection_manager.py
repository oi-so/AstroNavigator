from __future__ import annotations
from typing import Generic, TypeVar

from astronavigator.rendering.projection.projection import Projection


P = TypeVar("P")
C = TypeVar("C")


class ProjectionManager(Generic[P, C]):
    def __init__(self, projection: Projection[P, C]) -> None:
        self._projection = projection

    @property
    def projection(self) -> Projection[P, C]:
        return self._projection

    def create_context(self, scene) -> C:
        return self._projection.create_context(scene)