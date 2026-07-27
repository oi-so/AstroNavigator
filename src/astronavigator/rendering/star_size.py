from __future__ import annotations


import math

from astronavigator.sky.magnitude import Magnitude




def calculate_star_radius(magnitude: Magnitude) -> float:
    flux = 10 ** (-0.4 * magnitude.value)
    radius = 1.0 + 0.6 * math.log10(flux + 1)
    radius = min(radius, 12.0)

    return radius