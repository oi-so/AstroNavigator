from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from astronavigator.mount.e_zeus.e_zeus2 import EZeus2MountSettings
from astronavigator.sky.position import Position


class MountSettingsStore:
    def __init__(self, directory: Path | None = None):
        if directory is None:
            directory = Path.home() / ".astronavigator" / "mount_settings"
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)
        

    def load(self, id: str) -> EZeus2MountSettings | None:
        path = self._directory / f"{id}.json"
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return EZeus2MountSettings(
            reference_position=Position(**data["reference_position"]),
            reference_steps=tuple(data["reference_steps"]),
            ra_steps_per_rev=data.get("ra_steps_per_rev"),
            dec_steps_per_rev=data.get("dec_steps_per_rev"),
            ra_sign=data.get("ra_sign", 1),
            dec_sign=data.get("dec_sign", 1),
        )


    def save(self, id: str, settings: EZeus2MountSettings) -> None:
        path = self._directory / f"{id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, ensure_ascii=False, indent=4)