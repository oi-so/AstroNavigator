from __future__ import annotations

from dataclasses import dataclass, field
import serial


from astronavigator.mount.mount import Axis, ConnectionState, Mount, MountDevice
from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2Protocol, EZeus2StatusIndex, EZeus2_RA_DEC, EZeus2_Direction, EZeus2_Speed
from astronavigator.sky.position import Position


STEP_COUNTER_MODULO = 1 << 32
STEP_COUNTER_HALF = 1 << 31


# TODO:
# - 子午線反転
# - SideOfPier対応
# - SlewPath対応
# - RA/DECの符号確認
# - can_なんとかの実装


@dataclass(slots=True)
class EZeus2MountSettings:
    reference_position: Position = field(default_factory=lambda: Position(0.0, 0.0))
    reference_steps: tuple[int, int] = field(default_factory=lambda: (0, 0))
    ra_steps_per_rev: int | None = None
    dec_steps_per_rev: int | None = None
    ra_sign: int = 1
    dec_sign: int = 1


class EZeus2(Mount):
    def __init__(self, port: str) -> None:
        self._protocol = EZeus2Protocol(port)
        self._settings = EZeus2MountSettings()
        self._driver_name = None
        self._state = ConnectionState.DISCONNECTED
        self._e_zeus2_status = None

    def update_status(self) -> None:
        self._e_zeus2_status = self._protocol.get_status()

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def settings(self) -> EZeus2MountSettings:
        return self._settings

    @property
    def is_tracking(self) -> bool:
        status = self._e_zeus2_status
        if status is None:
            self.update_status()
            status = self._e_zeus2_status
        # TODO: 向き確認
        return (status[EZeus2StatusIndex.RA_DIRECTION] == "F" and status[EZeus2StatusIndex.RA_SPEED] == 1)

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
        status = self._e_zeus2_status
        if status is None:
            self.update_status()
            status = self._e_zeus2_status
        return (status[EZeus2StatusIndex.RA_STATUS] != "I" or status[EZeus2StatusIndex.DEC_STATUS] != "I")
    

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

        except Exception as e:
            self._state = ConnectionState.ERROR
            raise e


    def disconnect(self) -> None:
        self._protocol.disconnect()
        self._driver_name = None
        self._state = ConnectionState.DISCONNECTED

    def get_position(self) -> Position:
        ra_steps, dec_steps = self._protocol.get_position()
        return self._step_to_position(ra_steps, dec_steps)


    def _step_difference(self, new_steps: int, reference_steps: int) -> int:
        delta = (new_steps - reference_steps + STEP_COUNTER_HALF) % STEP_COUNTER_MODULO - STEP_COUNTER_HALF
        return delta

    def _step_to_position(self, ra_steps: int, dec_steps: int) -> Position:
        ra_steps_per_rev = self._settings.ra_steps_per_rev
        dec_steps_per_rev = self._settings.dec_steps_per_rev

        if ra_steps_per_rev is None or dec_steps_per_rev is None:
            raise RuntimeError("Steps per revolution not set")

        reference_ra_steps, reference_dec_steps = self._settings.reference_steps

        delta_ra_steps = self._step_difference(ra_steps, reference_ra_steps)
        delta_dec_steps = self._step_difference(dec_steps, reference_dec_steps)

        delta_ra_deg = (delta_ra_steps / ra_steps_per_rev) * 360.0 * self._settings.ra_sign
        delta_dec_deg = (delta_dec_steps / dec_steps_per_rev) * 360.0 * self._settings.dec_sign

        return self._settings.reference_position.moved(delta_ra_deg, delta_dec_deg)

    @staticmethod
    def _angle_difference(new_angle: float, reference_angle: float) -> float:
        delta = (new_angle - reference_angle + 180.0) % 360.0 - 180.0
        return delta


    def sync(self, position: Position) -> None:
        self._settings.reference_position = position
        self._settings.reference_steps = self._protocol.get_position()


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
        e_direction: EZeus2_Direction = (EZeus2_Direction.FORWARD if speed >= 0 else EZeus2_Direction.REVERSE)
        e_speed: EZeus2_Speed = self._convert_speed(abs(speed))
        self._protocol.drive(e_axis, e_direction, e_speed)

    def stop_axis(self, axis: Axis) -> None:
        e_axis = self._axis_to_e_axis(axis)
        self._protocol.drive(e_axis, EZeus2_Direction.FORWARD, EZeus2_Speed.STOP)

    def stop(self) -> None:
        self._protocol.stop()

    def set_tracking(self, tracking: bool) -> None:
            self._protocol.stop(to_siderial=tracking)


    def slew_to(self, position: Position) -> None:
        target_ra_steps, target_dec_steps = self._position_to_step(position)
        current_ra_steps, current_dec_steps = self._protocol.get_position()

        delta_ra_steps = self._step_difference(target_ra_steps, current_ra_steps)
        delta_dec_steps = self._step_difference(target_dec_steps, current_dec_steps)
        ra_direction = EZeus2_Direction.FORWARD if delta_ra_steps >= 0 else EZeus2_Direction.REVERSE
        dec_direction = EZeus2_Direction.FORWARD if delta_dec_steps >= 0 else EZeus2_Direction.REVERSE

        self._protocol.drive(EZeus2_RA_DEC.RA, ra_direction, EZeus2_Speed.FAST, abs(delta_ra_steps))
        self._protocol.drive(EZeus2_RA_DEC.DEC, dec_direction, EZeus2_Speed.FAST, abs(delta_dec_steps))

    def _position_to_step(self, position: Position) -> tuple[int, int]:
        ra_steps_per_rev = self._settings.ra_steps_per_rev
        dec_steps_per_rev = self._settings.dec_steps_per_rev

        if ra_steps_per_rev is None or dec_steps_per_rev is None:
            raise RuntimeError("Steps per revolution not set")

        reference_ra_steps, reference_dec_steps = self._settings.reference_steps
        reference_position = self._settings.reference_position

        # TODO: 最短距離か計算
        delta_ra_deg = self._angle_difference(position.ra_deg, reference_position.ra_deg)
        delta_dec_deg = self._angle_difference(position.dec_deg, reference_position.dec_deg)

        delta_ra_steps = int((delta_ra_deg / 360.0) * ra_steps_per_rev * self._settings.ra_sign)
        delta_dec_steps = int((delta_dec_deg / 360.0) * dec_steps_per_rev * self._settings.dec_sign)

        new_ra_steps = (reference_ra_steps + delta_ra_steps) % STEP_COUNTER_MODULO
        new_dec_steps = (reference_dec_steps + delta_dec_steps) % STEP_COUNTER_MODULO

        return new_ra_steps, new_dec_steps

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
                protocol.disconnect()

            except serial.SerialException:
                continue
            except Exception:
                continue

        return devices


    @classmethod
    def create(cls, identifier: str) -> Mount:
        mount = cls(identifier)
        return mount