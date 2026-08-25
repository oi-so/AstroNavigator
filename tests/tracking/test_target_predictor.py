from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import ClassVar

import pytest

from astronavigator.scene.observer import Observer
from astronavigator.scene.time import Time
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import SkyObject
from astronavigator.tracking import (
    SystemUtcTimeProvider,
    TargetPredictor,
)


@dataclass(slots=True)
class LinearSkyObject(SkyObject):
    reference_time_utc: datetime
    reference_ra_deg: float
    reference_dec_deg: float

    ra_rate_deg_per_sec: float
    dec_rate_deg_per_sec: float

    is_dynamic: ClassVar[bool] = True

    def get_position(
        self,
        time: Time | None = None,
        observer: Observer | None = None,
    ) -> Position:
        if time is None:
            raise ValueError("time is required.")

        elapsed_sec = (
            time.utc - self.reference_time_utc
        ).total_seconds()

        return Position(
            ra_deg=(
                self.reference_ra_deg
                + self.ra_rate_deg_per_sec * elapsed_sec
            ),
            dec_deg=(
                self.reference_dec_deg
                + self.dec_rate_deg_per_sec * elapsed_sec
            ),
        ).normalized()

    def get_magnitude(
        self,
        time: Time | None = None,
        observer: Observer | None = None,
    ) -> Magnitude:
        return Magnitude(0.0)


def create_target(
    *,
    reference_time_utc: datetime,
    reference_ra_deg: float = 10.0,
    reference_dec_deg: float = 20.0,
    ra_rate_deg_per_sec: float = 1.0,
    dec_rate_deg_per_sec: float = 0.5,
) -> LinearSkyObject:
    return LinearSkyObject(
        id="test:linear",
        name="Linear Target",
        object_type=ObjectType.SATELLITE,
        hip=None,
        reference_time_utc=reference_time_utc,
        reference_ra_deg=reference_ra_deg,
        reference_dec_deg=reference_dec_deg,
        ra_rate_deg_per_sec=ra_rate_deg_per_sec,
        dec_rate_deg_per_sec=dec_rate_deg_per_sec,
    )


def test_predicts_linear_position_and_rate() -> None:
    start_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )
    target = create_target(reference_time_utc=start_time)

    predictor = TargetPredictor()
    prediction = predictor.predict(
        target=target,
        observer=Observer.default(),
        current_time_utc=start_time,
        prediction_horizon_sec=2.0,
    )

    assert prediction.current_position.ra_deg == pytest.approx(10.0)
    assert prediction.current_position.dec_deg == pytest.approx(20.0)

    assert prediction.future_position.ra_deg == pytest.approx(12.0)
    assert prediction.future_position.dec_deg == pytest.approx(21.0)

    assert prediction.ra_rate_deg_per_sec == pytest.approx(1.0)
    assert prediction.dec_rate_deg_per_sec == pytest.approx(0.5)


def test_predictor_handles_ra_wraparound() -> None:
    start_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )
    target = create_target(
        reference_time_utc=start_time,
        reference_ra_deg=359.0,
        reference_dec_deg=0.0,
        ra_rate_deg_per_sec=2.0,
        dec_rate_deg_per_sec=0.0,
    )

    prediction = TargetPredictor().predict(
        target=target,
        observer=Observer.default(),
        current_time_utc=start_time,
        prediction_horizon_sec=1.0,
    )

    assert prediction.current_position.ra_deg == pytest.approx(359.0)
    assert prediction.future_position.ra_deg == pytest.approx(1.0)
    assert prediction.ra_rate_deg_per_sec == pytest.approx(2.0)
    assert prediction.angular_rate_deg_per_sec == pytest.approx(2.0)


def test_predictor_uses_time_offset() -> None:
    start_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )
    target = create_target(
        reference_time_utc=start_time,
        reference_ra_deg=10.0,
        reference_dec_deg=0.0,
        ra_rate_deg_per_sec=1.0,
        dec_rate_deg_per_sec=0.0,
    )

    provider = SystemUtcTimeProvider(
        now_function=lambda: start_time,
    )

    prediction = TargetPredictor().predict_from_provider(
        target=target,
        observer=Observer.default(),
        time_provider=provider,
        prediction_horizon_sec=1.0,
        time_offset_sec=2.0,
    )

    assert prediction.current_time_utc == (
        start_time + timedelta(seconds=2.0)
    )
    assert prediction.current_position.ra_deg == pytest.approx(12.0)


def test_predictor_normalizes_input_time_to_utc() -> None:
    utc_time = datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )
    japan_timezone = timezone(timedelta(hours=9))
    japan_time = utc_time.astimezone(japan_timezone)

    target = create_target(reference_time_utc=utc_time)

    prediction = TargetPredictor().predict(
        target=target,
        observer=Observer.default(),
        current_time_utc=japan_time,
        prediction_horizon_sec=1.0,
    )

    assert prediction.current_time_utc == utc_time


def test_predictor_rejects_naive_time() -> None:
    target = create_target(
        reference_time_utc=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError):
        TargetPredictor().predict(
            target=target,
            observer=Observer.default(),
            current_time_utc=datetime(2026, 8, 18, 12, 0),
            prediction_horizon_sec=1.0,
        )


def test_predictor_rejects_invalid_horizon() -> None:
    start_time = datetime.now(timezone.utc)
    target = create_target(reference_time_utc=start_time)

    with pytest.raises(ValueError):
        TargetPredictor().predict(
            target=target,
            observer=Observer.default(),
            current_time_utc=start_time,
            prediction_horizon_sec=0.0,
        )