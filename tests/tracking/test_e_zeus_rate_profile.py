from __future__ import annotations

from pathlib import Path

import pytest

from astronavigator.mount.e_zeus.e_zeus2_protocol import (
    EZeus2_Direction,
    EZeus2_Speed,
)
from astronavigator.mount.mount import Axis
from astronavigator.tracking.e_zeus_rate_profile import (
    EZeusRateOption,
    EZeusRateProfile,
)
from astronavigator.tracking.e_zeus_rate_profile_repository import (
    EZeusRateProfileRepository,
)


def create_profile(
    profile_id: str = "test-profile",
    name: str = "テストプロファイル",
) -> EZeusRateProfile:
    # ここでの値は単体テスト専用の仮値。
    # 実機へ送るレートとしては使用しない。
    return EZeusRateProfile(
        profile_id=profile_id,
        name=name,
        options=(
            EZeusRateOption(
                axis=Axis.RA,
                speed=EZeus2_Speed.SIDEREAL,
                drive_direction=EZeus2_Direction.FORWARD,
                axis_rate_deg_per_sec=-0.004,
            ),
            EZeusRateOption(
                axis=Axis.RA,
                speed=EZeus2_Speed.SLOW,
                drive_direction=EZeus2_Direction.FORWARD,
                axis_rate_deg_per_sec=0.1,
            ),
            EZeusRateOption(
                axis=Axis.DEC,
                speed=EZeus2_Speed.SLOW,
                drive_direction=EZeus2_Direction.REVERSE,
                axis_rate_deg_per_sec=-0.1,
            ),
            EZeusRateOption(
                axis=Axis.DEC,
                speed=EZeus2_Speed.SLOW,
                drive_direction=EZeus2_Direction.FORWARD,
                axis_rate_deg_per_sec=0.1,
            ),
        ),
    )


def create_repository(
    tmp_path: Path,
) -> EZeusRateProfileRepository:
    return EZeusRateProfileRepository(
        tmp_path / "e_zeus_rate_profiles.json"
    )


def test_missing_file_returns_empty_repository(
    tmp_path: Path,
) -> None:
    repository = create_repository(tmp_path)

    assert repository.list_profiles() == ()
    assert repository.get_selected_profile() is None


def test_profile_is_saved_and_loaded(
    tmp_path: Path,
) -> None:
    repository = create_repository(tmp_path)
    profile = create_profile()

    repository.save_profile(profile)

    loaded = repository.get_profile(profile.profile_id)

    assert loaded == profile


def test_selected_profile_is_persisted(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "profiles.json"
    first_repository = EZeusRateProfileRepository(file_path)

    profile = create_profile()
    first_repository.save_profile(
        profile,
        select=True,
    )

    second_repository = EZeusRateProfileRepository(file_path)

    assert (
        second_repository.get_selected_profile_id()
        == profile.profile_id
    )
    assert (
        second_repository.get_selected_profile()
        == profile
    )


def test_existing_profile_is_updated(
    tmp_path: Path,
) -> None:
    repository = create_repository(tmp_path)

    repository.save_profile(
        create_profile(name="変更前")
    )
    repository.save_profile(
        create_profile(name="変更後")
    )

    profiles = repository.list_profiles()

    assert len(profiles) == 1
    assert profiles[0].name == "変更後"


def test_delete_selected_profile_clears_selection(
    tmp_path: Path,
) -> None:
    repository = create_repository(tmp_path)
    profile = create_profile()

    repository.save_profile(
        profile,
        select=True,
    )
    repository.delete_profile(profile.profile_id)

    assert repository.list_profiles() == ()
    assert repository.get_selected_profile_id() is None


def test_duplicate_name_is_rejected(
    tmp_path: Path,
) -> None:
    repository = create_repository(tmp_path)

    repository.save_profile(
        create_profile(
            profile_id="first",
            name="同じ名前",
        )
    )

    with pytest.raises(ValueError):
        repository.save_profile(
            create_profile(
                profile_id="second",
                name="同じ名前",
            )
        )


def test_selecting_missing_profile_is_rejected(
    tmp_path: Path,
) -> None:
    repository = create_repository(tmp_path)

    with pytest.raises(KeyError):
        repository.select_profile("missing")


def test_invalid_json_is_reported(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "profiles.json"
    file_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    repository = EZeusRateProfileRepository(file_path)

    with pytest.raises(RuntimeError):
        repository.list_profiles()