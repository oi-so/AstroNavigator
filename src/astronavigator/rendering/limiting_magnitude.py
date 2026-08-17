from __future__ import annotations

import math

WIDE_FOV = 180.0


def calculate_limiting_magnitude(user_limit: float, fov: float) -> float:
    bonus = 1.4 * (math.log2(180 / fov))
    result = min(user_limit, 4.0 + bonus)

    return result


def calculate_label_limiting_magnitude(wide_fov_limit: float, max_limit: float, fov_deg: float) -> float:
    zoom_steps = max(0.0, math.log2(WIDE_FOV / fov_deg))
    result = min(max_limit, wide_fov_limit + zoom_steps * 1.1)
    return result