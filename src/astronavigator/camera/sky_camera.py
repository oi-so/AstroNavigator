from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


from astronavigator.sky.position import Position

ZOOM_FOV_DEG = 0.10
WIDE_FOV_DEG = 180.0


class CameraReferenceFrame(Enum):
    EQUATORAL = auto()
    HORIZONTAL = auto()
    AUTO = auto()


@dataclass(slots=True)
class SkyCamera:
    center: Position
    fov_deg: float
    rotation: float
    limit_magnitude: float = 25.0
    reference_frame: CameraReferenceFrame = CameraReferenceFrame.AUTO


    @classmethod
    def default(cls) -> "SkyCamera":
        return SkyCamera(
            center=Position(0, 0),
            fov_deg=90,
            rotation=0
        )
    
    def move(self, delta_ra: float, delta_dec: float):
        self.center = self.center.moved(delta_ra, delta_dec)

    def zoom(self, factor: float):
        self.fov_deg *= factor
        self.fov_deg = max(ZOOM_FOV_DEG, min(WIDE_FOV_DEG, self.fov_deg))