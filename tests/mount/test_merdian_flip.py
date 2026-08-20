from __future__ import annotations

import pytest

from astronavigator.mount.meridian_flip import (
    decide_meridian_flip,
    normalize_signed_degrees,
)
from astronavigator.mount.slew_path import PierSide


@pytest.mark.parametrize(
    ("angle_deg", "expected_deg"),
    [
        (0.0, 0.0),
        (10.0, 10.0),
        (350.0, -10.0),
        (190.0, -170.0),
        (-190.0, 170.0),
    ],
)
def test_normalize_signed_degrees(
    angle_deg: float,
    expected_deg: float,
) -> None:
    assert normalize_signed_degrees(angle_deg) == pytest.approx(
        expected_deg
    )


def test_target_west_of_meridian_requires_east_side() -> None:
    decision = decide_meridian_flip(
        hour_angle_deg=30.0,
        current_pier_side=PierSide.WEST,
    )

    assert decision.preferred_pier_side is PierSide.EAST
    assert decision.is_flip_required
    assert not decision.is_near_meridian


def test_target_east_of_meridian_requires_west_side() -> None:
    decision = decide_meridian_flip(
        hour_angle_deg=-30.0,
        current_pier_side=PierSide.EAST,
    )

    assert decision.preferred_pier_side is PierSide.WEST
    assert decision.is_flip_required
    assert not decision.is_near_meridian


def test_matching_side_does_not_require_flip() -> None:
    decision = decide_meridian_flip(
        hour_angle_deg=30.0,
        current_pier_side=PierSide.EAST,
    )

    assert decision.preferred_pier_side is PierSide.EAST
    assert not decision.is_flip_required


@pytest.mark.parametrize(
    "hour_angle_deg",
    [-20.0, -10.0, 0.0, 10.0, 20.0],
)
def test_near_meridian_requires_user_confirmation(
    hour_angle_deg: float,
) -> None:
    decision = decide_meridian_flip(
        hour_angle_deg=hour_angle_deg,
        current_pier_side=PierSide.EAST,
    )

    assert decision.is_near_meridian
    assert not decision.is_flip_required


def test_unknown_pier_side_is_rejected() -> None:
    with pytest.raises(RuntimeError):
        decide_meridian_flip(
            hour_angle_deg=30.0,
            current_pier_side=PierSide.UNKNOWN,
        )