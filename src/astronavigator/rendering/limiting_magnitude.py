from __future__ import annotations

import math



def calculate_limiting_magnitude(user_limit: float, fov: float) -> float:
    bonus = 1.4 * (math.log2(180 / fov))
    result = min(user_limit, 4.0 + bonus)
    print(f"result: {result} (user limit: {user_limit}, fov: {fov}, bonus: {bonus})")

    return result