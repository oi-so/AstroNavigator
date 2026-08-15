from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


from astronavigator.sky.position import Position


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
        self.fov_deg = max(1.0, min(180.0, self.fov_deg))  # Clamp FOV between 5 and 180 degrees