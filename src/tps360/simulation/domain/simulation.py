from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.threats.domain import Threat

from .clock import SimulationClock
from .context import SimulationContext
from .enums import SimulationStatus
from .scenario import Scenario
from .timeline import Timeline, TimelineEvent


@dataclass
class Simulation:
    """A simulation session for a community, threat, timeline, clock, and context snapshot."""

    id: UUID
    scenario: Scenario
    community: Community
    threat: Threat
    timeline: Timeline
    current_time: datetime
    status: SimulationStatus
    clock: SimulationClock
    context: SimulationContext

    def __post_init__(self) -> None:
        if self.current_time != self.clock.current_time:
            raise DomainRuleViolation("Simulation current time must match its clock.")

    def __setattr__(self, name: str, value: object) -> None:
        if (
            name == "context"
            and hasattr(self, "context")
            and self.status is not SimulationStatus.DRAFT
        ):
            raise DomainRuleViolation("Simulation context cannot change after start.")
        super().__setattr__(name, value)

    def start(self) -> None:
        if self.status is not SimulationStatus.DRAFT:
            raise DomainRuleViolation("Only draft simulations can be started.")
        self.context.validate_for_start()
        self.status = SimulationStatus.RUNNING

    def pause(self) -> None:
        if self.status is not SimulationStatus.RUNNING:
            raise DomainRuleViolation("Only running simulations can be paused.")
        self.status = SimulationStatus.PAUSED

    def resume(self) -> None:
        if self.status is not SimulationStatus.PAUSED:
            raise DomainRuleViolation("Only paused simulations can be resumed.")
        self.status = SimulationStatus.RUNNING

    def complete(self) -> None:
        if self.status is SimulationStatus.COMPLETED:
            raise DomainRuleViolation("Simulation is already completed.")
        self.status = SimulationStatus.COMPLETED

    def advance_time(self, minutes: int) -> tuple[TimelineEvent, ...]:
        if self.status is not SimulationStatus.RUNNING:
            raise DomainRuleViolation("Only running simulations can advance time.")
        self.current_time = self.clock.advance(minutes)
        return self.timeline.events_until(self.current_time)