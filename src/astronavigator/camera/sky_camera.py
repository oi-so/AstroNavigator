from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING

from astronavigator.rendering.projection.orthographic_projection import OrthographicProjection
from astronavigator.sky.position import Position

if TYPE_CHECKING:
    from astronavigator.rendering.projection.projection import Projection


@dataclass(slots=True)
class SkyCamera:
    center: Position
    fov: float
    rotation: float
    projection: Projection 


    @classmethod
    def default(cls) -> "SkyCamera":
        return SkyCamera(
            center=Position(0, 0),
            fov=90,
            rotation=0,
            projection=OrthographicProjection()
        )