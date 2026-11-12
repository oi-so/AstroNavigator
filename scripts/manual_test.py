from __future__ import annotations

import time

from astronavigator.mount.e_zeus.e_zeus2 import EZeus2
from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.position import Position


PORT = "COM3"

REFERENCE_POSITION = Position(
    ra_deg=120.0,
    dec_deg=20.0,
)

TARGET_POSITION = Position(
    ra_deg=122.0,
    dec_deg=22.0,
)


def main() -> None:
    mount = EZeus2(PORT)
    mount.connect()

    try:
        mount.set_tracking(True)

        mount.sync(
            REFERENCE_POSITION,
            pier_side=PierSide.EAST,
        )

        protocol = mount._protocol

        before = protocol.get_position()

        mount.slew_to(
            TARGET_POSITION,
            pier_side=PierSide.EAST,
        )

        # 加速が始まったところで緊急停止する
        time.sleep(0.3)
        mount.stop()

        immediately_after = protocol.get_position()
        status_after = protocol.get_status()

        time.sleep(1.0)

        one_second_after = protocol.get_position()
        status_later = protocol.get_status()

        print("開始GP:", before)
        print("停止直後GP:", immediately_after)
        print("1秒後GP:", one_second_after)

        print(
            "停止後の差:",
            (
                one_second_after[0]
                - immediately_after[0]
            ),
            (
                one_second_after[1]
                - immediately_after[1]
            ),
        )

        print("停止直後ST:", status_after)
        print("1秒後ST:", status_later)
        print("is_slewing:", mount.is_slewing)
        print("is_tracking:", mount.is_tracking)
        print("停止位置:", mount.position)

    finally:
        try:
            mount.stop()
        finally:
            mount.disconnect()


if __name__ == "__main__":
    main()