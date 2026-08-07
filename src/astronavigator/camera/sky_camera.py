from __future__ import annotations

from dataclasses import dataclass


from astronavigator.sky.position import Position


@dataclass(slots=True)
class SkyCamera:
    center: Position
    fov_deg: float
    rotation: float
    limit_magnitude: float = 6.0  # Default limit magnitude for visibility


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
        self.fov_deg = max(5.0, min(180.0, self.fov_deg))  # Clamp FOV between 5 and 180 degrees