from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.threats.domain import Threat

from .clock import SimulationClock
from .context import SimulationContext
from .enums import SimulationStatus
from .events import (
    SimulationCancelled,
    SimulationCompleted,
    SimulationDomainEvent,
    SimulationPaused,
    SimulationPrepared,
    SimulationResumed,
    SimulationStarted,
    SimulationTimeAdvanced,
)
from .scenario import Scenario
from .timeline import Timeline, TimelineEvent


@dataclass
class Simulation:
    """Aggregate root for an isolated simulation session and its lifecycle audit trail."""

    id: UUID
    scenario: Scenario
    community: Community
    threat: Threat
    timeline: Timeline
    current_time: datetime
    status: SimulationStatus
    clock: SimulationClock
    context: SimulationContext
    domain_events: tuple[SimulationDomainEvent, ...] = field(default_factory=tuple)
    audit_trail: tuple[SimulationDomainEvent, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.current_time != self.clock.current_time:
            raise DomainRuleViolation("Simulation current time must match its clock.")

    def __setattr__(self, name: str, value: object) -> None:
        if (
            hasattr(self, "status")
            and self.status in {SimulationStatus.COMPLETED, SimulationStatus.CANCELLED}
            and name in {"context", "clock", "current_time", "status", "domain_events", "audit_trail"}
        ):
            raise DomainRuleViolation("Completed or cancelled simulations cannot be changed.")
        if (
            name == "context"
            and hasattr(self, "context")
            and self.status in {
                SimulationStatus.RUNNING,
                SimulationStatus.PAUSED,
                SimulationStatus.COMPLETED,
                SimulationStatus.CANCELLED,
            }
        ):
            raise DomainRuleViolation("Simulation context cannot change after start.")
        super().__setattr__(name, value)

    def prepare(self) -> None:
        if self.status is not SimulationStatus.DRAFT:
            raise DomainRuleViolation("Only draft simulations can be prepared.")
        self.status = SimulationStatus.READY
        self._record(SimulationPrepared(self.id, self.current_time))

    def start(self) -> None:
        if self.status is not SimulationStatus.READY:
            raise DomainRuleViolation("Only ready simulations can be started.")
        self.context.validate_for_start()
        self.status = SimulationStatus.RUNNING
        self._record(SimulationStarted(self.id, self.current_time))

    def pause(self) -> None:
        if self.status is not SimulationStatus.RUNNING:
            raise DomainRuleViolation("Only running simulations can be paused.")
        self.status = SimulationStatus.PAUSED
        self._record(SimulationPaused(self.id, self.current_time))

    def resume(self) -> None:
        if self.status is not SimulationStatus.PAUSED:
            raise DomainRuleViolation("Only paused simulations can be resumed.")
        self.status = SimulationStatus.RUNNING
        self._record(SimulationResumed(self.id, self.current_time))

    def complete(self) -> None:
        if self.status not in {SimulationStatus.RUNNING, SimulationStatus.PAUSED}:
            raise DomainRuleViolation("Only running or paused simulations can be completed.")
        self._record(SimulationCompleted(self.id, self.current_time))
        self.status = SimulationStatus.COMPLETED

    def cancel(self) -> None:
        if self.status in {SimulationStatus.COMPLETED, SimulationStatus.CANCELLED}:
            raise DomainRuleViolation("Completed or cancelled simulations cannot be cancelled.")
        self._record(SimulationCancelled(self.id, self.current_time))
        self.status = SimulationStatus.CANCELLED

    def advance_time(self, minutes: int) -> tuple[TimelineEvent, ...]:
        if self.status is not SimulationStatus.RUNNING:
            raise DomainRuleViolation("Only running simulations can advance time.")
        advanced_clock = self.clock.advance(minutes)
        elapsed_minutes = (advanced_clock.current_time - self.current_time).total_seconds() / 60
        self.clock = advanced_clock
        self.current_time = advanced_clock.current_time
        self._record(
            SimulationTimeAdvanced(
                self.id,
                self.current_time,
                requested_minutes=minutes,
                elapsed_simulation_minutes=elapsed_minutes,
            )
        )
        return self.timeline.events_until(self.current_time)

    def _record(self, event: SimulationDomainEvent) -> None:
        self.domain_events = (*self.domain_events, event)
        self.audit_trail = (*self.audit_trail, event)


SimulationSession = Simulation