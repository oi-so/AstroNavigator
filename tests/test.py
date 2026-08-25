from __future__ import annotations

import time

from astronavigator.mount.e_zeus.e_zeus2 import EZeus2
from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2_Speed
from astronavigator.mount.mount import Axis
from astronavigator.mount.slew_path import MountAxisPosition, PierSide
from astronavigator.sky.position import Position


PORT = "/dev/cu.usbserial-A906VB1T"

SYNC_RA_DEG = 81.75
SYNC_DEC_DEG = 28.6
START_PIER_SIDE = PierSide.EAST

POLL_INTERVAL_SECONDS = 0.2
TIMEOUT_SECONDS = 300.0
TARGET_TOLERANCE_STEPS = 2


def get_axis_steps(
    steps: tuple[int, int],
    axis: Axis,
) -> int:
    return steps[0] if axis is Axis.RA else steps[1]


def wait_for_axis(
    mount: EZeus2,
    axis: Axis,
    target_steps: int,
) -> None:
    steps_per_rev = mount.get_steps_per_revolution(axis)
    started_at = time.monotonic()
    observed_slewing = False

    while True:
        current_steps = mount.get_raw_position_steps()
        current_axis_steps = get_axis_steps(current_steps, axis)

        error_steps = mount._step_difference(
            current_axis_steps,
            target_steps,
            steps_per_rev,
        )

        slewing = mount.is_slewing
        observed_slewing |= slewing

        print(
            f"\r{axis.name}: "
            f"current={current_axis_steps}, "
            f"target={target_steps}, "
            f"error={error_steps:+d}, "
            f"slewing={slewing}",
            end="",
            flush=True,
        )

        if not slewing and abs(error_steps) <= TARGET_TOLERANCE_STEPS:
            print()
            return

        if not slewing and observed_slewing:
            print()
            raise RuntimeError(
                f"{axis.name}軸が目標到着前に停止しました: "
                f"error={error_steps} steps"
            )

        if time.monotonic() - started_at > TIMEOUT_SECONDS:
            print()
            raise TimeoutError(f"{axis.name}軸の移動がタイムアウトしました")

        time.sleep(POLL_INTERVAL_SECONDS)


def move_axis_to_steps(
    mount: EZeus2,
    axis: Axis,
    target_steps: int,
    description: str,
) -> None:
    current_steps = mount.get_raw_position_steps()
    current_axis_steps = get_axis_steps(current_steps, axis)
    steps_per_rev = mount.get_steps_per_revolution(axis)

    delta_steps = mount._step_difference(
        target_steps,
        current_axis_steps,
        steps_per_rev,
    )

    if delta_steps == 0:
        print(f"{description}: 移動不要")
        return

    direction = mount._step_delta_to_direction(
        axis,
        delta_steps,
    )

    movement_deg = abs(delta_steps) / steps_per_rev * 360.0

    print()
    print(f"=== {description} ===")
    print(f"軸: {axis.name}")
    print(f"現在GP: {current_axis_steps}")
    print(f"目標GP: {target_steps}")
    print(f"移動量: {delta_steps:+,} steps ({movement_deg:.6f}°)")
    print(f"方向: {direction.name}")
    print()
    print("鏡筒・錘・ケーブルの経路を確認してください。")

    confirmation = input("この区間を動かす場合は MOVE と入力: ")
    if confirmation != "MOVE":
        raise RuntimeError("ユーザー操作により中止しました")


    e_axis = mount._axis_to_e_axis(axis)
    mount._protocol.drive(
        e_axis,
        direction,
        EZeus2_Speed.FAST,
        abs(delta_steps),
    )

    wait_for_axis(mount, axis, target_steps)


def main() -> None:
    mount = EZeus2(PORT)
    movement_started = False

    try:
        mount.connect()
        mount.set_tracking(False)

        sync_position = Position(
            ra_deg=SYNC_RA_DEG,
            dec_deg=SYNC_DEC_DEG,
        )

        mount.sync(
            sync_position,
            pier_side=START_PIER_SIDE,
        )

        start_steps = mount.get_raw_position_steps()
        start_axis_position = mount._steps_to_axis_position(*start_steps)

        # 今回は計画確認時とほぼ同じ時刻の目標を作る。
        target_axis_position = mount._sky_to_axis_position(
            sync_position,
            PierSide.WEST,
            mount.settings.reference_time_utc,
        )

        # 第1区間：
        # 現在のRA軸位置を保ったままDec軸を+90°へ
        pole_before_flip = MountAxisPosition(
            ra_axis_deg=start_axis_position.ra_axis_deg,
            dec_axis_deg=90.0,
        )
        pole_before_steps = mount._axis_position_to_steps(
            pole_before_flip,
        )

        # 第2区間：
        # Dec=90°のままRA軸だけ反転後の位置へ
        pole_after_flip = MountAxisPosition(
            ra_axis_deg=target_axis_position.ra_axis_deg,
            dec_axis_deg=90.0,
        )
        pole_after_steps = mount._axis_position_to_steps(
            pole_after_flip,
        )

        # 第3区間：
        # RA軸位置を保ったまま反転後のDec位置へ
        target_steps = mount._axis_position_to_steps(
            target_axis_position,
        )

        print("開始GP:", start_steps)
        print("極移動後GP:", pole_before_steps)
        print("RA反転後GP:", pole_after_steps)
        print("最終目標GP:", target_steps)

        input("何も動かしません。経路を確認したらEnterを押してください: ")

        movement_started = True

        move_axis_to_steps(
            mount,
            Axis.DEC,
            pole_before_steps[1],
            "区間1: Dec軸を極へ移動",
        )

        move_axis_to_steps(
            mount,
            Axis.RA,
            pole_after_steps[0],
            "区間2: 極を向いたままRA軸を180°回転",
        )

        move_axis_to_steps(
            mount,
            Axis.DEC,
            target_steps[1],
            "区間3: Dec軸を反転後の位置へ移動",
        )

        movement_started = False

        final_steps = mount.get_raw_position_steps()

        ra_error = mount._step_difference(
            final_steps[0],
            target_steps[0],
            mount.get_steps_per_revolution(Axis.RA),
        )
        dec_error = mount._step_difference(
            final_steps[1],
            target_steps[1],
            mount.get_steps_per_revolution(Axis.DEC),
        )

        print()
        print("=== 子午線反転試験完了 ===")
        print("開始GP:", start_steps)
        print("目標GP:", target_steps)
        print("終了GP:", final_steps)
        print("RA誤差:", ra_error, "steps")
        print("Dec誤差:", dec_error, "steps")
        print("計算上の現在座標:", mount.position)
        print()
        print("追尾は停止したままです。")

    except KeyboardInterrupt:
        print("\n緊急停止します")
        mount.stop()
        raise

    except Exception:
        if movement_started:
            mount.stop()
        raise

    finally:
        if mount.is_connected:
            mount.disconnect()


if __name__ == "__main__":
    main()