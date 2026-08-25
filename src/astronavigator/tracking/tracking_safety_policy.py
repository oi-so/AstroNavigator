from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import math

from astronavigator.tracking.tracking_plan import TrackingPlan
from astronavigator.tracking.tracking_state import TrackingPlanStatus, TrackingRunMode



class TrackingSafetyIssueCode(Enum):
    PLAN_BLOCKED = auto()

    MOUNT_DISCONNECTED = auto()
    MOUNT_NOT_SYNCHRONIZED = auto()
    COMMUNICATION_ERROR = auto()

    COLLISION_RISK = auto()
    MOUNT_LIMIT_REACHED = auto()
    BELOW_MINIMUM_ALTITUDE = auto()

    INVALID_TIME_RATE = auto()
    REAL_MOUNT_TIME_JUMP = auto()

    RA_RATE_LIMIT = auto()
    DEC_RATE_LIMIT = auto()


class TrackingSafetySeverity(Enum):
    WARNING = auto()
    BLOCKING = auto()
    STOP = auto()



@dataclass(frozen=True, slots=True)
class TrackingSafetyIssue:
    code: TrackingSafetyIssueCode
    severity: TrackingSafetySeverity
    message: str



@dataclass(frozen=True, slots=True)
class TrackingSafetyContext:
    run_mode: TrackingRunMode
    is_real_mount: bool

    mount_connected: bool = True
    mount_synchronized: bool = True
    communication_healthy: bool = True

    collision_risk: bool = False
    mount_limit_reached: bool = False

    time_rate: float = 1.0
    time_jump_requested: bool = False

    available_ra_rate_deg_per_sec: float | None = None
    available_dec_rate_deg_per_sec: float | None = None

    current_altitude_deg: float | None = None
    minimum_altitude_deg: float | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.time_rate):
            raise ValueError("time_rate must be finite.")

        self._validate_optional_non_negative(
            "available_ra_rate_deg_per_sec",
            self.available_ra_rate_deg_per_sec,
        )
        self._validate_optional_non_negative(
            "available_dec_rate_deg_per_sec",
            self.available_dec_rate_deg_per_sec,
        )
        self._validate_optional_finite(
            "current_altitude_deg",
            self.current_altitude_deg,
        )
        self._validate_optional_finite(
            "minimum_altitude_deg",
            self.minimum_altitude_deg,
        )

    @staticmethod
    def _validate_optional_non_negative(
        name: str,
        value: float | None,
    ) -> None:
        if value is None:
            return

        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

        if value < 0.0:
            raise ValueError(f"{name} must not be negative.")

    @staticmethod
    def _validate_optional_finite(
        name: str,
        value: float | None,
    ) -> None:
        if value is not None and not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")


@dataclass(frozen=True, slots=True)
class TrackingSafetyResult:
    status: TrackingPlanStatus
    issues: tuple[TrackingSafetyIssue, ...]

    @property
    def can_start(self) -> bool:
        return not any(
            issue.severity
            in {TrackingSafetySeverity.BLOCKING, TrackingSafetySeverity.STOP}
            for issue in self.issues
        )

    @property
    def should_stop(self) -> bool:
        return any(
            issue.severity is TrackingSafetySeverity.STOP for issue in self.issues
        )

    @property
    def warnings(self) -> tuple[TrackingSafetyIssue, ...]:
        return tuple(
            issue for issue in self.issues
            if issue.severity is TrackingSafetySeverity.WARNING
        )





class TrackingSafetyPolicy:
    _RATE_EPSILON = 1e-9
    _TIME_RATE_EPSILON = 1e-9

    def evaluate_before_start(self, plan: TrackingPlan, context: TrackingSafetyContext) -> TrackingSafetyResult:
        issues: list[TrackingSafetyIssue] = []

        if plan.status is TrackingPlanStatus.BLOCKED:
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.PLAN_BLOCKED,
                    severity=TrackingSafetySeverity.BLOCKING,
                    message=(plan.blocked_reason or "追尾計画が実行不可になっています。"),
                )
            )

        issues.extend(self._evaluate_mount_state(context, runtime=False))
        issues.extend(self._evaluate_time_mode(context, runtime=False))
        issues.extend(self._evaluate_rate_limits(plan, context))

        return self._create_result(plan.status, issues)

    def evaluate_during_tracking(self, plan: TrackingPlan, context: TrackingSafetyContext) -> TrackingSafetyResult:
        issues: list[TrackingSafetyIssue] = []

        issues.extend(self._evaluate_mount_state(context, runtime=True))
        issues.extend(self._evaluate_time_mode(context, runtime=True))
        issues.extend(self._evaluate_rate_limits(plan, context))
        issues.extend(self._evaluate_altitude(context))

        return self._create_result(plan.status, issues)


    def _evaluate_mount_state(self, context: TrackingSafetyContext, *, runtime: bool) -> list[TrackingSafetyIssue]:
        severity = (
            TrackingSafetySeverity.STOP if runtime else TrackingSafetySeverity.BLOCKING
        )

        issues: list[TrackingSafetyIssue] = []

        if not context.mount_connected:
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.MOUNT_DISCONNECTED,
                    severity=severity,
                    message="マウントが接続されていません。",
                )
            )

        if not context.mount_synchronized:
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.MOUNT_NOT_SYNCHRONIZED,
                    severity=severity,
                    message="マウントの位置同期が完了していません。",
                )
            )

        if not context.communication_healthy:
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.COMMUNICATION_ERROR,
                    severity=severity,
                    message="マウントとの通信に異常があります。",
                )
            )

        if context.collision_risk:
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.COLLISION_RISK,
                    severity=severity,
                    message="鏡筒または架台が衝突する危険があります。",
                )
            )

        if context.mount_limit_reached:
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.MOUNT_LIMIT_REACHED,
                    severity=severity,
                    message="マウントの可動限界に達しています。",
                )
            )

        return issues

    def _evaluate_time_mode(self, context: TrackingSafetyContext, *, runtime: bool,) -> list[TrackingSafetyIssue]:
        issues: list[TrackingSafetyIssue] = []

        time_rate_must_be_real = (
            context.run_mode is TrackingRunMode.OBSERVATION
            or context.is_real_mount
        )

        if time_rate_must_be_real and not math.isclose(context.time_rate, 1.0, abs_tol=self._TIME_RATE_EPSILON):
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.INVALID_TIME_RATE,
                    severity=(
                        TrackingSafetySeverity.STOP
                        if runtime
                        else TrackingSafetySeverity.BLOCKING
                    ),
                    message=(
                        "観測モードまたは実機接続中は、"
                        "時刻倍率を1倍にしてください。"
                    ),
                )
            )

        if context.is_real_mount and context.time_jump_requested:
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.REAL_MOUNT_TIME_JUMP,
                    severity=TrackingSafetySeverity.STOP if runtime else TrackingSafetySeverity.BLOCKING,
                    message="実機接続中の追尾では、Scene時刻をジャンプできません。",
                )
            )

        return issues

    def _evaluate_rate_limits(self, plan: TrackingPlan, context: TrackingSafetyContext) -> list[TrackingSafetyIssue]:
        issues: list[TrackingSafetyIssue] = []

        ra_available = context.available_ra_rate_deg_per_sec
        if ra_available is not None and plan.maximum_required_ra_rate_deg_per_sec > ra_available + self._RATE_EPSILON:
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.RA_RATE_LIMIT,
                    severity=TrackingSafetySeverity.WARNING,
                    message="必要なRA軸速度が利用可能な最大速度を超えています。最大速度で追尾を続けます。",
                )
            )

        dec_available = context.available_dec_rate_deg_per_sec
        if (
            dec_available is not None
            and plan.maximum_required_dec_rate_deg_per_sec
            > dec_available + self._RATE_EPSILON
        ):
            issues.append(
                TrackingSafetyIssue(
                    code=TrackingSafetyIssueCode.DEC_RATE_LIMIT,
                    severity=TrackingSafetySeverity.WARNING,
                    message="必要なDec軸速度が利用可能な最大速度を超えています。最大速度で追尾を続けます。"
                )
            )

        return issues

    def _evaluate_altitude(self, context: TrackingSafetyContext) -> list[TrackingSafetyIssue]:
        if (
            context.current_altitude_deg is None or context.minimum_altitude_deg is None
            or context.current_altitude_deg >= context.minimum_altitude_deg
        ):
            return []

        return [
            TrackingSafetyIssue(
                code=TrackingSafetyIssueCode.BELOW_MINIMUM_ALTITUDE,
                severity=TrackingSafetySeverity.STOP,
                message="対象天体が追尾終了高度を下回りました。",
            )
        ]

    @staticmethod
    def _create_result(original_status: TrackingPlanStatus, issues: list[TrackingSafetyIssue]) -> TrackingSafetyResult:
        if any(
            issue.severity in {TrackingSafetySeverity.BLOCKING, TrackingSafetySeverity.STOP}
            for issue in issues
        ):
            status = TrackingPlanStatus.BLOCKED
        elif (
            original_status is TrackingPlanStatus.DEGRADED
            or any(
                issue.severity is TrackingSafetySeverity.WARNING
                for issue in issues
            )
        ):
            status = TrackingPlanStatus.DEGRADED
        else:
            status = TrackingPlanStatus.READY

        return TrackingSafetyResult(
            status=status,
            issues=tuple(issues),
        )