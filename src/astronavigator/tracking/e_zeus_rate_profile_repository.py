from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2_Speed
from astronavigator.mount.mount import Axis
from astronavigator.tracking.e_zeus_rate_profile import EZeusRateOption,EZeusRateProfile


FILE_FORMAT_VERSION = 1


@dataclass(frozen=True, slots=True)
class _ProfileDocument:
    profiles: tuple[EZeusRateProfile, ...]
    selected_profile_id: str | None


@dataclass
class EZeusRateProfileRepository:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    @property
    def file_path(self) -> Path:
        return self._file_path

    def list_profiles(self) -> tuple[EZeusRateProfile, ...]:
        document = self._load_document()
        return tuple(sorted(document.profiles, key=lambda profile: profile.name.casefold()))

    def get_profile(self, profile_id: str) -> EZeusRateProfile | None:
        for profile in self._load_document().profiles:
            if profile.profile_id == profile_id:
                return profile

            return None

    
    def get_selected_profile_id(self) -> str | None:
        return self._load_document().selected_profile_id

    def get_selected_profile(self) -> EZeusRateProfile | None:
        document = self._load_document()
        selected_id = document.selected_profile_id
        if selected_id is None:
            return None

        for profile in document.profiles:
            if profile.profile_id == selected_id:
                return profile

        return None


    def save_profile(self, profile: EZeusRateProfile, *, select: bool = False) -> None:
        document = self._load_document()
        profiles = list(document.profiles)
        self._validate_unique_name(profile, profiles)

        replaced = False

        for index, existing in enumerate(profiles):
            if existing.profile_id == profile.profile_id:
                profiles[index] = profile
                replaced = True
                break

        if not replaced:
            profiles.append(profile)


        selected_profile_id = profile.profile_id if select else document.selected_profile_id

        self._write_document(
            _ProfileDocument(
                profiles=tuple(profiles),
                selected_profile_id=selected_profile_id,
            )
        )

    def delete_profile(self, profile_id: str) -> None:
        document = self._load_document()
        profiles = [p for p in document.profiles if p.profile_id != profile_id]

        if len(profiles) == len(document.profiles):
            raise ValueError(f"No profile found with ID '{profile_id}'.")

        selected_profile_id = None if document.selected_profile_id == profile_id else document.selected_profile_id

        self._write_document(
            _ProfileDocument(
                profiles=tuple(profiles),
                selected_profile_id=selected_profile_id,
            )
        )


    def select_profile(self, profile_id: str | None) -> None:
        document = self._load_document()

        if profile_id is not None and not any(p.profile_id == profile_id for p in document.profiles):
            raise KeyError(f"No profile found with ID '{profile_id}'.")

        self._write_document(
            _ProfileDocument(
                profiles=document.profiles,
                selected_profile_id=profile_id,
            )
        )


    @staticmethod
    def _validate_unique_name(profile: EZeusRateProfile, profiles: list[EZeusRateProfile]) -> None:
        requested_name = profile.name.strip().casefold()

        for existing in profiles:
            if existing.profile_id == profile.profile_id:
                continue

            if existing.name.strip().casefold() == requested_name:
                raise ValueError(f"A profile with the name '{profile.name}' already exists.")


    def _load_document(self) -> _ProfileDocument:
        if not self._file_path.exists():
            return _ProfileDocument(profiles=(), selected_profile_id=None)

        try:
            raw_document = json.loads(self._file_path.read_text(encoding="utf-8"))

        except (OSError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to read or parse the profile file: {e}") from e

        if not isinstance(raw_document, dict):
            raise ValueError("Invalid profile file format: expected a JSON object.")

        version = raw_document.get("version")
        if version != FILE_FORMAT_VERSION:
            raise ValueError(f"Unsupported profile file version: {version}")

        raw_profiles = raw_document.get("profiles")
        if not isinstance(raw_profiles, list):
            raise ValueError("Invalid profile file format: 'profiles' must be a list.")
        try:
            profiles = tuple(self._deserialize_profile(raw_profile) for raw_profile in raw_profiles)
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"Invalid profile data: {e}") from e

        selected_profile_id = raw_document.get("selected_profile_id")
        if selected_profile_id is not None and not isinstance(selected_profile_id, str):
            raise ValueError("Invalid profile file format: 'selected_profile_id' must be a string or null.")

        if selected_profile_id is not None and not any(p.profile_id == selected_profile_id for p in profiles):
            selected_profile_id = None

        return _ProfileDocument(
            profiles=profiles,
            selected_profile_id=selected_profile_id
        )

    def _write_document(self, document: _ProfileDocument) -> None:
        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        raw_document = {
            "version": FILE_FORMAT_VERSION,
            "selected_profile_id": (
                document.selected_profile_id
            ),
            "profiles": [
                self._serialize_profile(profile)
                for profile in document.profiles
            ],
        }

        temporary_path = self._file_path.with_suffix(self._file_path.suffix + ".tmp")

        try:
            temporary_path.write_text(
                json.dumps(raw_document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(self._file_path)
        except OSError as error:
            raise RuntimeError(
                "E-ZEUS IIレートプロファイルを"
                f"保存できませんでした: {self._file_path}"
            ) from error

    @staticmethod
    def _serialize_profile(
        profile: EZeusRateProfile,
    ) -> dict[str, Any]:
        options = sorted(
            profile.options,
            key=lambda option: (
                option.axis.value,
                option.speed.value,
                option.coordinate_direction,
            ),
        )

        return {
            "profile_id": profile.profile_id,
            "name": profile.name,
            "options": [
                {
                    "axis": option.axis.name,
                    "speed": option.speed.name,
                    "coordinate_direction": (
                        option.coordinate_direction
                    ),
                    "axis_rate_deg_per_sec": (
                        option.axis_rate_deg_per_sec
                    ),
                }
                for option in options
            ],
        }

    @staticmethod
    def _deserialize_profile(raw_profile: Any,) -> EZeusRateProfile:
        if not isinstance(raw_profile, dict):
            raise TypeError("Each profile must be an object.")

        raw_options = raw_profile["options"]
        if not isinstance(raw_options, list):
            raise TypeError("profile options must be an array.")

        options: list[EZeusRateOption] = []

        for raw_option in raw_options:
            if not isinstance(raw_option, dict):
                raise TypeError("Each rate option must be an object.")

            options.append(
                EZeusRateOption(
                    axis=Axis[raw_option["axis"]],
                    speed=EZeus2_Speed[raw_option["speed"]],
                    coordinate_direction=int(raw_option["coordinate_direction"]),
                    axis_rate_deg_per_sec=float(raw_option["axis_rate_deg_per_sec"]),
                )
            )

        return EZeusRateProfile(
            profile_id=str(raw_profile["profile_id"]),
            name=str(raw_profile["name"]),
            options=tuple(options),
        )