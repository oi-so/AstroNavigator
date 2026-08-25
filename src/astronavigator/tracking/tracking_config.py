from __future__ import annotations

from dataclasses import dataclass
import math

from astronavigator.tracking.tracking_state import MeridianStrategy



@dataclass(frozen=True, slots=True)
class TrackingConfig:
    entry_altitude_deg: float = 10.5
    exit_altitude_deg: float = 10.0

    preposition_lead_time: float = 30.0
    acquisition_tolerance_deg: float = 0.5
    acquisition_timeout: float = 10.0

    prediction_interval: float = 0.2
    prediction_horizon: float = 1.0

    max_session_sec: float | None = None
    meridian_strategy: MeridianStrategy = MeridianStrategy.AVOID_DURING_TRACKING

    rate_profile_id: str | None = None


    def __post_init__(self) -> None:
        self._validate_finite_values()

        if not 0.0 <= self.exit_altitude_deg <= 90.0:
            raise ValueError(f"exit_altitude_deg must be in [0, 90], got {self.exit_altitude_deg}")

        if not 0.0 <= self.entry_altitude_deg <= 90.0:
            raise ValueError(f"entry_altitude_deg must be in [0, 90], got {self.entry_altitude_deg}")

        if self.exit_altitude_deg > self.entry_altitude_deg:
            raise ValueError(f"exit_altitude_deg must be <= entry_altitude_deg, got {self.exit_altitude_deg} > {self.entry_altitude_deg}")

        if self.preposition_lead_time < 0.0:
            raise ValueError(f"preposition_lead_time must be non-negative, got {self.preposition_lead_time}")

        if not 0.0 <= self.acquisition_tolerance_deg <= 180.0:
            raise ValueError(f"acquisition_tolerance_deg must be in [0, 180], got {self.acquisition_tolerance_deg}")

        if self.acquisition_timeout <= 0.0:
            raise ValueError(f"acquisition_timeout must be positive, got {self.acquisition_timeout}")

        if self.prediction_interval <= 0.0:
            raise ValueError(f"prediction_interval must be positive, got {self.prediction_interval}")

        if self.prediction_horizon <= 0.0:
            raise ValueError(f"prediction_horizon must be positive, got {self.prediction_horizon}")

        if self.prediction_horizon < self.prediction_interval:
            raise ValueError(f"prediction_horizon must be >= prediction_interval, got {self.prediction_horizon} < {self.prediction_interval}")

        if self.max_session_sec is not None and self.max_session_sec <= 0.0:
            raise ValueError(f"max_session_sec must be positive if specified, got {self.max_session_sec}")

        if self.rate_profile_id is not None and not self.rate_profile_id.strip():
            raise ValueError(f"rate_profile_id must be a non-empty string if specified, got '{self.rate_profile_id}'")


    def _validate_finite_values(self) -> None:
        values = {
            "entry_altitude_deg": self.entry_altitude_deg,
            "exit_altitude_deg": self.exit_altitude_deg,
            "preposition_lead_time": self.preposition_lead_time,
            "acquisition_tolerance_deg": self.acquisition_tolerance_deg,
            "acquisition_timeout": self.acquisition_timeout,
            "prediction_interval": self.prediction_interval,
            "prediction_horizon": self.prediction_horizon,
        }

        if self.max_session_sec is not None:
            values["max_session_sec"] = self.max_session_sec

        for name, value in values.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be a finite number, got {value}")


