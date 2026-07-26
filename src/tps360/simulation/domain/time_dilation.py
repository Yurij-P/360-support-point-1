from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tps360.core.exceptions import DomainRuleViolation


class CrisisVelocity(StrEnum):
    """Simulation time compression ratio based on crisis dynamics and velocity."""

    FAST = "FAST"  # 1:30 — 1 real minute = 30 simulated minutes (Fires, Military attacks, Flash floods)
    MODERATE = "MODERATE"  # 1:60 — 1 real minute = 60 simulated minutes (1 hr) (Cholera outbreaks, Water contamination)
    SLOW_MAX = "SLOW_MAX"  # 1:90 — 1 real minute = 90 simulated minutes (1.5 hrs) (Livestock mortality, Quarantine isolation, Blackouts)


# Mapping of standard threat and crisis types to their default velocity
CRISIS_TYPE_VELOCITY_MAPPING: dict[str, CrisisVelocity] = {
    "FIRE": CrisisVelocity.FAST,
    "MILITARY_ATTACK": CrisisVelocity.FAST,
    "FLASH_FLOOD": CrisisVelocity.FAST,
    "CHOLERA": CrisisVelocity.MODERATE,
    "WATER_CONTAMINATION": CrisisVelocity.MODERATE,
    "CHEMICAL_SPILL": CrisisVelocity.MODERATE,
    "LIVESTOCK_MORTALITY": CrisisVelocity.SLOW_MAX,
    "QUARANTINE_ISOLATION": CrisisVelocity.SLOW_MAX,
    "BLACKOUT": CrisisVelocity.SLOW_MAX,
}


def resolve_crisis_velocity(crisis_type: str) -> CrisisVelocity:
    normalized = crisis_type.strip().upper()
    return CRISIS_TYPE_VELOCITY_MAPPING.get(normalized, CrisisVelocity.MODERATE)


@dataclass(frozen=True)
class SimulationRoundClock:
    """Immutable clock manager calculating time dilation between real server time and simulation time."""

    real_round_minutes: int  # Real-world facilitator round length (5 to 30 minutes)
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
