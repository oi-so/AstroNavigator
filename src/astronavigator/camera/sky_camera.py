from __future__ import annotations

from dataclasses import dataclass

from astronavigator.rendering.projection.projection import Projection
from astronavigator.sky.position import Position


@dataclass(slots=True)
class SkyCamera:
    center: Position
    fov: float
    rotation: float
    projection: Projection 