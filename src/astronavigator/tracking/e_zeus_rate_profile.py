from __future__ import annotations

from dataclasses import dataclass
import math

from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2_Direction, EZeus2_Speed
from astronavigator.mount.mount import Axis


@dataclass(frozen=True, slots=True)
class EZeusRateOption:
    axis: Axis
    speed: EZeus2_Speed

    # E-ZEUS IIへ実際に送るF/R指令
    drive_direction: EZeus2_Direction

    # 実測された架台軸座標上の速度
    axis_rate_deg_per_sec: float

    def __post_init__(self) -> None:
        if self.speed is EZeus2_Speed.STOP:
            raise ValueError("speed must not be STOP")

        if self.axis is Axis.DEC and self.speed is EZeus2_Speed.SIDEREAL:
            raise ValueError("DEC axis cannot use SIDEREAL speed")

        if not math.isfinite(self.axis_rate_deg_per_sec):
            raise ValueError(f"axis_rate_deg_per_sec must be finite, got {self.axis_rate_deg_per_sec}")

        if self.axis_rate_deg_per_sec == 0.0:
            raise ValueError(
                "Zero-rate commands must be omitted because "
                "STOP already represents zero axis rate."
            )

    @property
    def coordinate_direction(self) -> int:
        return 1 if self.axis_rate_deg_per_sec > 0.0 else -1

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
                    option.drive_direction.value,
                ),
            )
        )

        object.__setattr__(self, "options", normalized_options)

        keys: set[tuple[Axis, EZeus2_Speed, EZeus2_Direction]] = set()

        for option in self.options:
            key = (
                option.axis,
                option.speed,
                option.drive_direction,
            )

            if key in keys:
                raise ValueError(
                    "Duplicate option for "
                    f"axis={option.axis}, "
                    f"speed={option.speed}, "
                    f"drive_direction={option.drive_direction}"
                )

            keys.add(key)

        for axis in (Axis.RA, Axis.DEC):
            if not self.options_for_axis(axis):
                raise ValueError(f"No options provided for axis {axis}")

    def options_for_axis(self, axis: Axis) -> tuple[EZeusRateOption, ...]:
        return tuple(option for option in self.options if option.axis == axis)

    def options_for_direction(self, axis: Axis, direction: int) -> tuple[EZeusRateOption, ...]:
        if direction not in (-1, 1):
            raise ValueError(
                f"direction must be -1 or 1, got {direction}"
            )

        return tuple(
            option
            for option in self.options
            if option.axis is axis
            and option.coordinate_direction == direction
        )