from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import serial


from astronavigator.mount.mount import Axis, ConnectionState, Mount, MountDevice
from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2Protocol, EZeus2StatusIndex, EZeus2_RA_DEC, EZeus2_Direction, EZeus2_Speed
from astronavigator.sky.position import Position
from astronavigator.mount.slew_path import PierSide, MountAxisPosition


SIDEREAL_DAY_SECONDS = 86164.0905
PIER_SIDE_STEP_TOLERANCE = 2


# TODO:
# - 子午線反転
# - SideOfPier対応
# - SlewPath対応
# - RA/DECの符号確認
# - can_なんとかの実装


@dataclass(slots=True)
class EZeus2MountSettings:
    reference_steps: tuple[int, int] | None = None
    reference_axis_position: MountAxisPosition | None = None
    reference_time_utc: datetime | None = None

    pier_side: PierSide = PierSide.UNKNOWN

    ra_steps_per_rev: int | None = None
    dec_steps_per_rev: int | None = None

    ra_coordinate_sign: int = -1
    dec_coordinate_sign: int = 1

    ra_forward_step_sign: int = 1
    dec_forward_step_sign: int = 1


class EZeus2(Mount):
    def __init__(self, port: str) -> None:
        self._protocol = EZeus2Protocol(port)
        self._settings = EZeus2MountSettings()
        self._driver_name = None
        self._state = ConnectionState.DISCONNECTED
        self._e_zeus2_status = None

        self._pending_pier_side: PierSide | None = None
        self._pending_target_steps: tuple[int, int] | None = None
        self._pending_slew_observed = False

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def settings(self) -> EZeus2MountSettings:
        return self._settings

    @property
    def is_tracking(self) -> bool:
        status = self._protocol.get_status()
        self._apply_status(status)
        return status[EZeus2StatusIndex.RA_STATUS] == "I" and status[EZeus2StatusIndex.RA_SPEED] == EZeus2_Speed.SIDEREAL.value

    @property
    def driver_name(self) -> str:
        if self._driver_name is None:
            raise RuntimeError("Mount is not connected, driver name is not available")
        return self._driver_name

    @property
    def position(self) -> Position:
        return self.get_position()

    @property
    def is_slewing(self) -> bool:
        status = self._protocol.get_status()
        self._apply_status(status)
        return self._status_is_slewing(status)

    @property
    def pier_side(self) -> PierSide:
        return self._settings.pier_side

    @property
    def can_set_pier_side(self) -> bool:
        return True
    

    def connect(self) -> None:
        self._state = ConnectionState.CONNECTING

        try:
            self._protocol.connect()

            ra_steps_per_rev, dec_steps_per_rev = self._protocol.get_revolution_step()

            if ra_steps_per_rev <= 0 or dec_steps_per_rev <= 0:
                raise RuntimeError(
                    "Invalid steps per revolution received from mount"
                    f" (RA: {ra_steps_per_rev}, DEC: {dec_steps_per_rev})"
                )
            
            self._settings.ra_steps_per_rev = ra_steps_per_rev
            self._settings.dec_steps_per_rev = dec_steps_per_rev
            self._driver_name = self._protocol.get_version()

            self._state = ConnectionState.CONNECTED

        except Exception:
            self._state = ConnectionState.ERROR
            raise


    def disconnect(self) -> None:
        self._protocol.disconnect()
        self._driver_name = None
        self._clear_pending_pier_change()
        self._settings.reference_steps = None
        self._settings.reference_axis_position = None
        self._settings.reference_time_utc = None
        self._settings.pier_side = PierSide.UNKNOWN

        self._state = ConnectionState.DISCONNECTED

    def get_position(self) -> Position:
        ra_steps, dec_steps = self._protocol.get_position()
        axis_position = self._steps_to_axis_position(ra_steps, dec_steps)
        return self._axis_to_sky_position(axis_position, datetime.now(timezone.utc))


    def _step_difference(self, new_steps: int, reference_steps: int, steps_per_rev: int) -> int:
        half_revolution = steps_per_rev / 2.0
        delta = (new_steps - reference_steps + half_revolution) % steps_per_rev - half_revolution
        return round(delta)

    def _steps_to_axis_position(self, ra_steps: int, dec_steps: int) -> MountAxisPosition:
        settings = self._settings

        reference_steps, reference_axis_position, _ = self._require_synced()

        ra_steps_per_rev = settings.ra_steps_per_rev
        dec_steps_per_rev = settings.dec_steps_per_rev

        if ra_steps_per_rev is None or dec_steps_per_rev is None:
            raise RuntimeError("Steps per revolution not set")

        reference_ra_steps, reference_dec_steps = reference_steps

        delta_ra_steps = self._step_difference(ra_steps, reference_ra_steps, ra_steps_per_rev)
        delta_dec_steps = self._step_difference(dec_steps, reference_dec_steps, dec_steps_per_rev)

        delta_ra_deg = (delta_ra_steps / ra_steps_per_rev) * 360.0 * settings.ra_coordinate_sign
        delta_dec_deg = (delta_dec_steps / dec_steps_per_rev) * 360.0 * settings.dec_coordinate_sign

        return MountAxisPosition(
            ra_axis_deg=self._normalize_angle(reference_axis_position.ra_axis_deg + delta_ra_deg),
            dec_axis_deg=self._normalize_signed_angle(reference_axis_position.dec_axis_deg + delta_dec_deg)
        )

    @staticmethod
    def _angle_difference(new_angle: float, reference_angle: float) -> float:
        delta = (new_angle - reference_angle + 180.0) % 360.0 - 180.0
        return delta


    def sync(self, position: Position, *, pier_side: PierSide | None = None) -> None:
        if pier_side == PierSide.UNKNOWN or pier_side is None:
            raise ValueError("Cannot sync with unknown pier side")

        now = datetime.now(timezone.utc)

        self._settings.reference_time_utc = now
        reference_axis_position = self._sky_to_axis_position(position, pier_side, now)
        self._settings.reference_steps = self._protocol.get_position()
        self._settings.reference_axis_position = reference_axis_position
        self._settings.pier_side = pier_side
        self._clear_pending_pier_change()


    def _convert_speed(self, speed: float) -> EZeus2_Speed:
        if not (0.0 <= speed <= 1.0):
            raise ValueError(f"Speed must be between 0.0 and 1.0, got {speed}")

        if speed == 0.0:
            return EZeus2_Speed.STOP
        elif speed < 0.3:
            return EZeus2_Speed.SLOW
        elif speed < 0.7:
            return EZeus2_Speed.MEDIUM
        elif speed <= 1.0:
            return EZeus2_Speed.FAST
        else:
            raise ValueError(f"Invalid speed value: {speed}")

    def _axis_to_e_axis(self, axis: Axis) -> EZeus2_RA_DEC:
        if axis == Axis.RA:
            return EZeus2_RA_DEC.RA
        elif axis == Axis.DEC:
            return EZeus2_RA_DEC.DEC
        else:
            raise ValueError(f"Invalid axis: {axis}")


    def move_axis(self, axis: Axis, speed: float) -> None:
        e_axis = self._axis_to_e_axis(axis)
        e_speed = self._convert_speed(abs(speed))

        if speed == 0.0:
            self._protocol.drive(e_axis, EZeus2_Direction.FORWARD, EZeus2_Speed.STOP)
            return

        self.move_axis_discrete(axis, 1 if speed > 0 else -1, e_speed)

    def stop_axis(self, axis: Axis) -> None:
        e_axis = self._axis_to_e_axis(axis)
        self._protocol.drive(e_axis, EZeus2_Direction.FORWARD, EZeus2_Speed.STOP)
        self._clear_pending_pier_change()

    def stop(self) -> None:
        self._protocol.stop()
        self._clear_pending_pier_change()

    def set_tracking(self, tracking: bool) -> None:
            self._protocol.stop(to_siderial=tracking)


    def slew_to(self, position: Position, *, pier_side: PierSide | None = None) -> None:
        self._require_synced()

        target_pier_side = self.pier_side if pier_side is None else pier_side
        if target_pier_side == PierSide.UNKNOWN:
            raise ValueError("Cannot slew with unknown pier side")

        now = datetime.now(timezone.utc)
        target_axis_position = self._sky_to_axis_position(position, target_pier_side, now)
        target_ra_steps, target_dec_steps = self._axis_position_to_steps(target_axis_position)
        current_ra_steps, current_dec_steps = self._protocol.get_position()

        ra_steps_per_rev = self._settings.ra_steps_per_rev
        dec_steps_per_rev = self._settings.dec_steps_per_rev

        if ra_steps_per_rev is None or dec_steps_per_rev is None:
            raise RuntimeError("Steps per revolution not set")

        delta_ra_steps = self._step_difference(target_ra_steps, current_ra_steps, ra_steps_per_rev)
        delta_dec_steps = self._step_difference(target_dec_steps, current_dec_steps, dec_steps_per_rev)

        pier_side_change = target_pier_side != self.pier_side

        if pier_side_change:
            self._pending_pier_side = target_pier_side
            self._pending_target_steps = (
                target_ra_steps,
                target_dec_steps,
            )
            self._pending_slew_observed = False

        try:
            if delta_ra_steps != 0:
                ra_direction = self._step_delta_to_direction(Axis.RA, delta_ra_steps,)
                self._protocol.drive(EZeus2_RA_DEC.RA, ra_direction, EZeus2_Speed.FAST, abs(delta_ra_steps))

            if delta_dec_steps != 0:
                dec_direction = self._step_delta_to_direction(Axis.DEC, delta_dec_steps)
                self._protocol.drive(EZeus2_RA_DEC.DEC, dec_direction, EZeus2_Speed.FAST, abs(delta_dec_steps))

        except Exception:
            if pier_side_change:
                self._clear_pending_pier_change()
            raise


    def _clear_pending_pier_change(self) -> None:
        self._pending_pier_side = None
        self._pending_target_steps = None
        self._pending_slew_observed = False

    def _axis_position_to_steps(self, axis_position: MountAxisPosition) -> tuple[int, int]:
        settings = self._settings
        reference_steps, reference_axis_position, _ = self._require_synced()
        ra_steps_per_rev = settings.ra_steps_per_rev
        dec_steps_per_rev = settings.dec_steps_per_rev

        if ra_steps_per_rev is None or dec_steps_per_rev is None:
            raise RuntimeError("Steps per revolution not set")
        reference_ra_steps, reference_dec_steps = reference_steps

        delta_ra_deg = self._angle_difference(axis_position.ra_axis_deg, reference_axis_position.ra_axis_deg)
        delta_dec_deg = self._angle_difference(axis_position.dec_axis_deg, reference_axis_position.dec_axis_deg)

        delta_ra_steps = round((delta_ra_deg / 360.0) * ra_steps_per_rev / settings.ra_coordinate_sign)
        delta_dec_steps = round((delta_dec_deg / 360.0) * dec_steps_per_rev / settings.dec_coordinate_sign)

        return (reference_ra_steps + delta_ra_steps) % ra_steps_per_rev, (reference_dec_steps + delta_dec_steps) % dec_steps_per_rev

    def home(self) -> None:
        raise NotImplementedError("Home operation is not supported for E-ZEUS2 mount")


    @property
    def can_sync(self) -> bool:
        return True


    @property
    def can_slew(self) -> bool:
        return True

    @property
    def can_home(self) -> bool:
        return False

    @property
    def can_move_axis(self) -> bool:
        return True



    @classmethod
    def discover(cls) -> list[MountDevice]:
        devices = []

        for port in cls.find_ports():
            try:
                protocol = EZeus2Protocol(port)
                version = protocol.quick_check()

                if version is None:
                    continue

                identifier = port
                devices.append(MountDevice(name=f"E-ZEUS2 ({version})", identifier=identifier, driver=cls))

            except serial.SerialException:
                continue
            except Exception:
                continue

        return devices


    @classmethod
    def create(cls, identifier: str) -> Mount:
        mount = cls(identifier)
        return mount


    def _forward_step_sign(self, axis: Axis) -> int:
        if axis == Axis.RA:
            sign =  self._settings.ra_forward_step_sign
        elif axis == Axis.DEC:
            sign =  self._settings.dec_forward_step_sign
        else:
            raise ValueError(f"Invalid axis: {axis}")

        if sign not in (-1, 1):
            raise ValueError(f"Invalid sign: {sign}, must be -1 or 1")

        return sign

    def _step_delta_to_direction(self, axis: Axis, delta_steps: int) -> EZeus2_Direction:
        if delta_steps == 0:
            raise ValueError("Step delta cannot be zero for direction determination")

        forward_step_sign = self._forward_step_sign(axis)
        if delta_steps * forward_step_sign > 0:
            return EZeus2_Direction.FORWARD
        else:
            return EZeus2_Direction.REVERSE


    @staticmethod
    def _normalize_angle(angle_deg: float) -> float:
        return angle_deg % 360.0

    @staticmethod
    def _normalize_signed_angle(angle_deg: float) -> float:
        return (angle_deg + 180.0) % 360.0 - 180.0

    def _sidereal_elapsed_deg(self, now: datetime) -> float:
        reference_time = self._settings.reference_time_utc

        if reference_time is None:
            raise RuntimeError("Reference time is not set in mount settings")

        elapsed_seconds = (now - reference_time).total_seconds()
        return elapsed_seconds * 360.0 / SIDEREAL_DAY_SECONDS

    def _sky_to_axis_position(self, position: Position, pier_side: PierSide, now: datetime) -> MountAxisPosition:
        sidereal_elapsed_deg = self._sidereal_elapsed_deg(now)

        ra_axis_deg = position.ra_deg - sidereal_elapsed_deg
        dec_axis_deg = position.dec_deg

        if pier_side == PierSide.WEST:
            ra_axis_deg += 180.0
            dec_axis_deg = 180.0 - position.dec_deg
        elif pier_side != PierSide.EAST:
            raise ValueError(f"Invalid pier side: {pier_side}")

        return MountAxisPosition(
            ra_axis_deg=self._normalize_angle(ra_axis_deg),
            dec_axis_deg=self._normalize_signed_angle(dec_axis_deg)
        )

    def _axis_to_sky_position(self, axis_position: MountAxisPosition, now: datetime) -> Position:
        sidereal_elapsed_deg = self._sidereal_elapsed_deg(now)
        ra_deg = axis_position.ra_axis_deg + sidereal_elapsed_deg
        dec_deg = axis_position.dec_axis_deg

        if dec_deg > 90.0:
            dec_deg = 180.0 - dec_deg
            ra_deg += 180.0
        elif dec_deg < -90.0:
            dec_deg = -180.0 - dec_deg
            ra_deg += 180.0

        return Position(
            ra_deg=self._normalize_angle(ra_deg),
            dec_deg=dec_deg
        )


    def _require_synced(self) -> tuple[tuple[int, int], MountAxisPosition, datetime]:
        settings = self._settings

        if settings.reference_steps is None or settings.reference_axis_position is None or settings.reference_time_utc is None or settings.pier_side == PierSide.UNKNOWN:
            raise RuntimeError("Mount is not synced. Please perform a sync operation first.")

        return (settings.reference_steps, settings.reference_axis_position, settings.reference_time_utc)



    @staticmethod
    def _status_is_slewing(states: dict) -> bool:
        return (states[EZeus2StatusIndex.RA_STATUS] != "I" or states[EZeus2StatusIndex.DEC_STATUS] != "I")

    def _apply_status(self, status: dict) -> None:
        self._e_zeus2_status = status
        if self._pending_pier_side is None or self._pending_target_steps is None:
            return

        if self._status_is_slewing(status):
            self._pending_slew_observed = True
            return

        current_ra_steps, current_dec_steps = self._protocol.get_position()
        target_ra_steps, target_dec_steps = self._pending_target_steps

        ra_steps_per_rev = self._settings.ra_steps_per_rev
        dec_steps_per_rev = self._settings.dec_steps_per_rev

        if ra_steps_per_rev is None or dec_steps_per_rev is None:
            raise RuntimeError("Steps per revolution not set")
        
        ra_error = abs(self._step_difference(current_ra_steps, target_ra_steps, ra_steps_per_rev))
        dec_error = abs(self._step_difference(current_dec_steps, target_dec_steps, dec_steps_per_rev))
        reached_target = ra_error <= PIER_SIDE_STEP_TOLERANCE and dec_error <= PIER_SIDE_STEP_TOLERANCE

        if reached_target:
            self._settings.pier_side = self._pending_pier_side
            self._clear_pending_pier_change()
        elif self._pending_slew_observed:
            self._clear_pending_pier_change()

    def update_status(self) -> None:
        status = self._protocol.get_status()
        self._apply_status(status)

    @property
    def requires_pier_side_for_sync(self) -> bool:
        return True

    @property
    def is_synced(self) -> bool:
        settings = self._settings
        return (
            settings.reference_steps is not None and
            settings.reference_axis_position is not None and
            settings.reference_time_utc is not None and
            settings.pier_side != PierSide.UNKNOWN
        )



    def move_axis_discrete(self, axis: Axis, coordinate_direction: int, speed: EZeus2_Speed) -> None:
        if coordinate_direction not in (-1, 1):
            raise ValueError("coordinate_direction must be -1 or 1")

        coordinate_sign = (
            self._settings.ra_coordinate_sign
            if axis is Axis.RA
            else self._settings.dec_coordinate_sign
        )
        forward_step_sign = self._forward_step_sign(axis)
        forward_coordinate_sign = coordinate_sign * forward_step_sign

        drive_direction = (
            EZeus2_Direction.FORWARD
            if coordinate_direction == forward_coordinate_sign
            else EZeus2_Direction.REVERSE
        )

        self.drive_axis_discrete(axis, drive_direction, speed)

    def drive_axis_discrete(self, axis: Axis, direction: EZeus2_Direction, speed: EZeus2_Speed) -> None:
        if not self.is_connected:
            raise RuntimeError("Mount is not connected")

        if axis is Axis.DEC and speed is EZeus2_Speed.SIDEREAL:
            raise ValueError("DEC axis cannot use SIDEREAL speed")

        if speed is EZeus2_Speed.STOP:
            self.stop_axis(axis)
            return

        self._protocol.drive(self._axis_to_e_axis(axis), direction, speed)



    def get_raw_position_steps(self) -> tuple[int, int]:
        if not self.is_connected:
            raise RuntimeError("Mount is not connected")

        return self._protocol.get_position()


    def get_steps_per_revolution(self, axis: Axis) -> int:
        if not self.is_connected:
            raise RuntimeError("Mount is not connected")

        value = self._settings.ra_steps_per_rev if axis is Axis.RA else self._settings.dec_steps_per_rev

        if value is None or value <= 0:
            raise RuntimeError("Steps per revolution not set")

        return value


    def get_coordinate_sign(self, axis: Axis) -> int:
        sign = self._settings.ra_coordinate_sign if axis is Axis.RA else self._settings.dec_coordinate_sign
        if sign not in (-1, 1):
            raise RuntimeError(f"Invalid coordinate sign for {axis.name}: {sign}")
        return sign