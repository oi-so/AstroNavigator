from __future__ import annotations

import time

from astronavigator.mount.e_zeus.e_zeus2_protocol import (
    EZeus2Protocol,
    EZeus2_Direction,
    EZeus2_RA_DEC,
    EZeus2_Speed,
)


PORT = "/dev/cu.usbserial-A906VB1T"


STEP_COUNTER_MODULO = 1 << 32
STEP_COUNTER_HALF = 1 << 31

DRIVE_SECONDS = 3


def step_difference(
    new_steps: int,
    reference_steps: int,
    steps_per_rev: int,
) -> int:
    half_steps_per_rev = steps_per_rev / 2.0
    return round((new_steps - reference_steps + half_steps_per_rev) % steps_per_rev - half_steps_per_rev)


def test_direction(
    protocol: EZeus2Protocol,
    axis: EZeus2_RA_DEC,
    direction: EZeus2_Direction,
    steps_per_rev: int
) -> None:
    print(f"\nTesting {axis.value} {direction.value}")

    before = protocol.get_position()
    print("before:", before)

    # ステップ数を指定せず、連続駆動
    protocol.drive(
        axis,
        direction,
        EZeus2_Speed.SLOW,
    )

    time.sleep(DRIVE_SECONDS)

    # 軸を停止
    protocol.drive(
        axis,
        EZeus2_Direction.FORWARD,
        EZeus2_Speed.STOP,
    )

    time.sleep(0.5)

    after = protocol.get_position()
    print("after:", after)

    index = (
        0 if axis == EZeus2_RA_DEC.RA else 1
    )

    ra_steps_per_rev, dec_steps_per_rev = protocol.get_revolution_step()

    print("steps per rev:", ra_steps_per_rev, dec_steps_per_rev)

    difference = step_difference(
        after[index],
        before[index],
        steps_per_rev,
    )

    print(
        f"{axis.value} {direction.value}: "
        f"difference={difference}"
    )

    print("status:", protocol.get_status())
    time.sleep(1.0)


def test_ra_reverse(
    protocol: EZeus2Protocol,
    ra_steps_per_rev: int,
) -> None:
    protocol.stop(to_siderial=False)
    time.sleep(1.0)

    before = protocol.get_position()
    print("before:", before)

    protocol.drive(
        EZeus2_RA_DEC.RA,
        EZeus2_Direction.REVERSE,
        EZeus2_Speed.SLOW,
    )

    for index in range(6):
        time.sleep(0.5)

        current = protocol.get_position()
        status = protocol.get_status()

        difference = step_difference(
            current[0],
            before[0],
            ra_steps_per_rev,
        )

        print(
            f"{(index + 1) * 0.5:.1f}s:",
            f"position={current[0]}",
            f"difference={difference}",
            f"status={status}",
        )

    protocol.drive(
        EZeus2_RA_DEC.RA,
        EZeus2_Direction.FORWARD,
        EZeus2_Speed.STOP,
    )

    time.sleep(0.5)


def main() -> None:
    protocol = EZeus2Protocol(PORT)
    protocol.connect()

    try:
        # 恒星追尾を停止
        protocol.stop(to_siderial=False)
        time.sleep(1.0)

        print("initial status:", protocol.get_status())
        print("initial position:", protocol.get_position())

        ra_steps_per_rev, dec_steps_per_rev = protocol.get_revolution_step()

        test_ra_reverse(protocol, ra_steps_per_rev)


        test_direction(
            protocol,
            EZeus2_RA_DEC.RA,
            EZeus2_Direction.FORWARD,
            ra_steps_per_rev
        )

        test_direction(
            protocol,
            EZeus2_RA_DEC.RA,
            EZeus2_Direction.REVERSE,
            ra_steps_per_rev
        )

        test_direction(
            protocol,
            EZeus2_RA_DEC.DEC,
            EZeus2_Direction.FORWARD,
            dec_steps_per_rev
        )

        test_direction(
            protocol,
            EZeus2_RA_DEC.DEC,
            EZeus2_Direction.REVERSE,
            dec_steps_per_rev
        )

    finally:
        protocol.stop(to_siderial=True)
        protocol.disconnect()


if __name__ == "__main__":
    main()