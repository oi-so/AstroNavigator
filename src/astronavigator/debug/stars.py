from __future__ import annotations

import random


from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import Star
from astronavigator.sky.object_tree import ObjectType


def crate_test_stars() -> list[Star]:
        stars = []

        index = 0

        for dec in range(-60, 61, 30):
            for ra in range(0, 360, 30):
                stars.append(
                    Star(
                        id=f"star_{index}",
                        name=f"Star {index}",
                        object_type=ObjectType.STAR,
                        _position=Position(
                            ra_deg=ra,
                            dec_deg=dec,
                        ),
                        _magnitude=Magnitude(random.randint(-1, 6)),
                    )
                )
                index += 1

        return stars