from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from tps360.core.exceptions import DomainRuleViolation


@dataclass(frozen=True)
class SimulationClock:
    """An immutable, deterministic clock for simulated time."""

    start_time: datetime
    current_time: datetime
    acceleration_factor: float = 1.0

    def __post_init__(self) -> None:
        if self.current_time < self.start_time:
            raise DomainRuleViolation("Simulation clock cannot precede its start time.")
        if self.acceleration_factor <= 0:
            raise DomainRuleViolation("Simulation clock acceleration must be positive.")

    def advance(self, minutes: int) -> SimulationClock:
        """Return a new clock advanced by accelerated simulated minutes."""
        if minutes < 0:
            raise DomainRuleViolation("Simulation clock cannot advance by negative minutes.")
        return SimulationClock(
            start_time=self.start_time,
            current_time=self.current_time + timedelta(minutes=minutes * self.acceleration_factor),
            acceleration_factor=self.acceleration_factor,
        )

    def reset(self) -> SimulationClock:
        """Return a new clock reset to the deterministic simulation start time."""
        return SimulationClock(
            start_time=self.start_time,
            current_time=self.start_time,
            acceleration_factor=self.acceleration_factor,
        )