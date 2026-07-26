from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tps360.core.exceptions import DomainRuleViolation


class CrisisVelocity(StrEnum):
    """Simulation time compression ratio based on crisis dynamics and velocity."""

    FAST = "FAST"  # 1:30 — 1 real minute = 30 simulated minutes (Fast events: fires, military, flash floods)
    MODERATE = "MODERATE"  # 1:60 — 1 real minute = 60 simulated minutes (1 hr) (Epidemiological: cholera, water contamination, spills)
    SLOW_MAX = "SLOW_MAX"  # 1:90 — 1 real minute = 90 simulated minutes (1.5 hrs) (Epizootic, quarantine, infrastructure, blackouts)


def resolve_crisis_velocity(
    crisis_type: str,
    override_velocity: CrisisVelocity | None = None,
) -> CrisisVelocity:
    """Dynamic crisis velocity resolution supporting arbitrary crisis types and optional admin/moderator override."""
    if override_velocity is not None:
        return override_velocity

    normalized = crisis_type.strip().lower()

    # Fast-velocity keywords
    if any(k in normalized for k in ("fire", "пожеж", "military", "обстріл", " flood", "падок", "вибух")):
        return CrisisVelocity.FAST

    # Slow-max keywords (epizootic, quarantine, blackout, infrastructure)
    if any(
        k in normalized
        for k in (
            "livestock",
            "худоб",
            "падіж",
            "епізоот",
            "quarantine",
            "ізоляц",
            "карантин",
            "blackout",
            "блек-аут",
            "інфраструктур",
            "сибірка",
        )
    ):
        return CrisisVelocity.SLOW_MAX

    # Default moderate velocity for general/biological/chemical/open-source crisis types
    return CrisisVelocity.MODERATE


@dataclass(frozen=True)
class SimulationRoundClock:
    """Immutable clock manager calculating time dilation between real server time and simulation time."""

    real_round_minutes: int  # Real-world round length (5 to 30 minutes)
    velocity: CrisisVelocity = CrisisVelocity.MODERATE

    def __post_init__(self) -> None:
        if self.real_round_minutes < 5 or self.real_round_minutes > 30:
            raise DomainRuleViolation("Real round duration must be between 5 and 30 minutes.")

    @property
    def simulated_minutes_per_real_minute(self) -> int:
        return {
            CrisisVelocity.FAST: 30,
            CrisisVelocity.MODERATE: 60,
            CrisisVelocity.SLOW_MAX: 90,
        }[self.velocity]

    @property
    def total_simulated_minutes_per_round(self) -> int:
        return self.real_round_minutes * self.simulated_minutes_per_real_minute

    @property
    def total_simulated_hours_per_round(self) -> float:
        return self.total_simulated_minutes_per_round / 60.0

    def simulated_seconds_passed(self, elapsed_real_seconds: float) -> float:
        if elapsed_real_seconds < 0:
            raise DomainRuleViolation("Elapsed real seconds cannot be negative.")
        return elapsed_real_seconds * self.simulated_minutes_per_real_minute
