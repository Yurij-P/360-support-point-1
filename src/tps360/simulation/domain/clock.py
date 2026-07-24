from dataclasses import dataclass
from datetime import datetime, timedelta

from tps360.core.exceptions import DomainRuleViolation


@dataclass
class SimulationClock:
    """A mutable clock that drives simulated time."""

    start_time: datetime
    current_time: datetime

    def __post_init__(self) -> None:
        if self.current_time < self.start_time:
            raise DomainRuleViolation("Simulation clock cannot precede its start time.")

    def advance(self, minutes: int) -> datetime:
        if minutes < 0:
            raise DomainRuleViolation("Simulation clock cannot advance by negative minutes.")
        self.current_time += timedelta(minutes=minutes)
        return self.current_time

    def reset(self) -> datetime:
        self.current_time = self.start_time
        return self.current_time