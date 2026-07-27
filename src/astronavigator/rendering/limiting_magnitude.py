from __future__ import annotations

import math



def calculate_limiting_magnitude(user_limit: float, fov: float) -> float:
    bonus = math.log2(90 / fov)

    return min(user_limit, 4.0 + bonus)