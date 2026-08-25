from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any

from astronavigator.mount.slew_path import PierSide


MERIDIAN_CONFIRMATION_MARGIN_DEG = 20.0


@dataclass(frozen=True, slots=True)
class MerdianFlipDecision:
    hour_angle_deg: float

    current_pier_side: PierSide
    preferred_pier_side: PierSide

    is_near_meridian: bool
    is_flip_required: bool


def normalize_signed_degrees(degrees: float) -> float:
    return (degrees + 180.0) % 360.0 - 180.0


def calculate_local_sidereal_time_deg(utc: datetime, longitude_deg: float, timescale: Any) -> float:
    if utc.tzinfo is None or utc.utcoffset() is None:
        raise ValueError(
            "UTC datetime must be timezone-aware."
        )

    utc_datetime = utc.astimezone(timezone.utc)
    skyfield_time = timescale.from_datetime(utc_datetime)

    greenwich_sidereal_deg = skyfield_time.gast * 15.0

    return (greenwich_sidereal_deg + longitude_deg) % 360.0



def calculate_hour_angle_deg(*, ra_deg: float, utc: datetime, longitude_deg: float, timescale: Any) -> float:
    local_sidereal_deg = calculate_local_sidereal_time_deg(utc, longitude_deg, timescale)
    hour_angle_deg = normalize_signed_degrees(local_sidereal_deg - ra_deg)
    return hour_angle_deg


def decide_meridian_flip(*, hour_angle_deg: float, current_pier_side: PierSide, confirmation_margin_deg: float = MERIDIAN_CONFIRMATION_MARGIN_DEG) -> MerdianFlipDecision:
    if not math.isfinite(hour_angle_deg):
        raise ValueError("Hour angle must be a finite number.")

    if not 0.0 <= confirmation_margin_deg < 180.0:
        raise ValueError("Confirmation margin must be between 0 and 90 degrees.")

    if current_pier_side == PierSide.UNKNOWN:
        raise RuntimeError("Current pier side must be known.")


    normalized_hour_angle = normalize_signed_degrees(hour_angle_deg)

    preferred_pier_side = PierSide.EAST if normalized_hour_angle >= 0.0 else PierSide.WEST
    is_near_meridian = abs(normalized_hour_angle) <= confirmation_margin_deg

    if_flip_required = not is_near_meridian and preferred_pier_side != current_pier_side

    return MerdianFlipDecision(
        hour_angle_deg=normalized_hour_angle,
        current_pier_side=current_pier_side,
        preferred_pier_side=preferred_pier_side,
        is_near_meridian=is_near_meridian,
        is_flip_required=if_flip_required
    )


def opposite_pier_side(pier_side: PierSide) -> PierSide:
    if pier_side == PierSide.EAST:
        return PierSide.WEST
    elif pier_side == PierSide.WEST:
        return PierSide.EAST
    else:
        raise ValueError("Cannot determine opposite pier side for unknown pier side.")