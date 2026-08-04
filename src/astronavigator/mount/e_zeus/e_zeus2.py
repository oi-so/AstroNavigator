from __future__ import annotations
from dataclasses import dataclass, field

from astronavigator.mount.mount import Mount
from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2Protocol
from astronavigator.sky.position import Position


STEP_COUNTER_MODULO = 1 << 32
STEP_COUNTER_HALF = 1 << 31


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

    @property
    def settings(self) -> EZeus2MountSettings:
        return self._settings

    def connect(self) -> None:
        self._protocol.connect()

        ra_steps_per_rev, dec_steps_per_rev = self._protocol.get_revolution_step()

        if ra_steps_per_rev <= 0 or dec_steps_per_rev <= 0:
            raise RuntimeError(
                "Invalid steps per revolution received from mount"
                f" (RA: {ra_steps_per_rev}, DEC: {dec_steps_per_rev})"
            )
        
        self._settings.ra_steps_per_rev = ra_steps_per_rev
        self._settings.dec_steps_per_rev = dec_steps_per_rev

    def disconnect(self) -> None:
        self._protocol.disconnect()
        

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


    def sync(self, position: Position) -> None:
        self._settings.reference_position = position
        self._settings.reference_steps = self._protocol.get_position()