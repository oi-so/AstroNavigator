from __future__ import annotations

from dataclasses import dataclass
import math

from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2_Speed
from astronavigator.mount.mount import Axis


@dataclass(frozen=True, slots=True)
class EZeusRateOption:
    axis: Axis
    speed: EZeus2_Speed

    coordinate_direction: int
    axis_rate_deg_per_sec: float

    def __post_init__(self) -> None:
        if self.coordinate_direction not in (-1, 1):
            raise ValueError(
                f"coordinate_direction must be -1 or 1, got {self.coordinate_direction}"
            )

        if self.speed is EZeus2_Speed.STOP:
            raise ValueError("speed must not be STOP")

        if self.axis is Axis.DEC and self.speed is EZeus2_Speed.SIDEREAL:
            raise ValueError("DEC axis cannot use SIDEREAL speed")

        if not math.isfinite(self.axis_rate_deg_per_sec):
            raise ValueError(
                f"axis_rate_deg_per_sec must be finite, got {self.axis_rate_deg_per_sec}"
            )

        if self.axis_rate_deg_per_sec == 0.0:
            raise ValueError(
                f"axis_rate_deg_per_sec must be non-zero, got {self.axis_rate_deg_per_sec}"
            )

        actual_direction = 1 if self.axis_rate_deg_per_sec > 0.0 else -1
        if actual_direction != self.coordinate_direction:
            raise ValueError(
                f"coordinate_direction ({self.coordinate_direction}) does not match "
                f"the sign of axis_rate_deg_per_sec ({self.axis_rate_deg_per_sec})"
            )

@dataclass(frozen=True, slots=True)
class EZeusRateProfile:
    profile_id: str
    name: str
    options: tuple[EZeusRateOption, ...]

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise ValueError("profile_id must not be empty")

        if not self.name.strip():
            raise ValueError("name must not be empty")

        normalized_options = tuple(
            sorted(
                self.options,
                key=lambda option: (
                    0 if option.axis is Axis.RA else 1,
                    option.speed.value,
                    option.coordinate_direction,
                ),
            )
        )

        object.__setattr__(self, "options", normalized_options)

        keys :set[tuple[Axis, EZeus2_Speed, int]] = set()

        for option in self.options:
            key = (option.axis, option.speed, option.coordinate_direction)
            if key in keys:
                raise ValueError(
                    f"Duplicate option for axis={option.axis}, speed={option.speed}, "
                    f"coordinate_direction={option.coordinate_direction}"
                )
            keys.add(key)

        for axis in (Axis.RA, Axis.DEC):
            if not self.options_for_axis(axis):
                raise ValueError(f"No options provided for axis {axis}")

    def options_for_axis(self, axis: Axis) -> tuple[EZeusRateOption, ...]:
        return tuple(option for option in self.options if option.axis == axis)

    def options_for_direction(self, axis: Axis, direction: int) -> tuple[EZeusRateOption, ...]:
        return tuple(
            option for option in self.options
            if option.axis == axis and option.coordinate_direction == direction
        )