from __future__ import annotations


import math

from astronavigator.sky.magnitude import Magnitude




def calculate_star_radius(magnitude: Magnitude, camera_fov_deg: float) -> float:
    flux = 10 ** (-0.2 * magnitude.value)
    radius = 1.0 + 4.0 * math.log2(flux + 1)

    scale = math.sqrt(90.0 / camera_fov_deg)
    scale = max(0.8, min(scale, 1.6))

    radius *= scale
    radius = min(radius, 12.0)

    return radius