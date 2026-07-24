from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.threats.domain import Threat

from .clock import SimulationClock
from .context import SimulationContext
from .enums import ScenarioRuntimeStatus, SimulationStatus
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

if TYPE_CHECKING:
    from .decision_engine import (
        DecisionEngine,
        DecisionOutcome,
        DecisionRequest,
        DecisionSubmission,
    )
    from .event_scheduler import EventRuntime, EventScheduler, SchedulerState
    from .scenario_definition import ScenarioDefinition
    from .scenario_runtime import ScenarioRuntime
    from .scenario_validation import ScenarioValidationResult


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
    scenario_runtime: ScenarioRuntime | None = None
    event_scheduler: EventScheduler | None = None
    decision_engine: DecisionEngine | None = None

    def __post_init__(self) -> None:
        if self.current_time != self.clock.current_time:
            raise DomainRuleViolation("Simulation current time must match its clock.")

    def __setattr__(self, name: str, value: object) -> None:
        if (
            hasattr(self, "status")
            and self.status in {SimulationStatus.COMPLETED, SimulationStatus.CANCELLED}
            and name
            in {
                "context",
                "clock",
                "current_time",
                "status",
                "domain_events",
                "audit_trail",
                "scenario_runtime",
                "event_scheduler",
                "decision_engine",
            }
        ):
            raise DomainRuleViolation("Completed or cancelled simulations cannot be changed.")
        if (
            name == "context"
            and hasattr(self, "context")
            and self.status
            in {
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
        if (
            self.event_scheduler is not None
            and self.scenario_runtime is not None
            and self.scenario_runtime.status is ScenarioRuntimeStatus.ACTIVE
        ):
            from .event_scheduler import SchedulerState

            self.event_scheduler.refresh(self, self.scenario_runtime, SchedulerState())
        return self.timeline.events_until(self.current_time)

    def load_scenario(self, definition: ScenarioDefinition) -> ScenarioRuntime:
        """Create an independent scenario runtime for this simulation session."""
        if self.status in {SimulationStatus.COMPLETED, SimulationStatus.CANCELLED}:
            raise DomainRuleViolation("Final simulations cannot load scenarios.")
        if self.scenario_runtime is not None:
            raise DomainRuleViolation("A simulation session can have only one main scenario runtime.")
        from .scenario_runtime import ScenarioRuntime

        self.scenario_runtime = ScenarioRuntime.load(self.id, definition, self.current_time)
        return self.scenario_runtime

    def validate_scenario(
        self, available_team_roles: tuple[str, ...]
    ) -> ScenarioValidationResult:
        if self.scenario_runtime is None:
            raise DomainRuleViolation("Simulation has no loaded scenario runtime.")
        from .scenario_validation import ScenarioCompatibilityPolicy

        result = ScenarioCompatibilityPolicy.validate(
            self.scenario_runtime.definition,
            self,
            available_team_roles,
        )
        self.scenario_runtime.validate(result, self.current_time)
        return result

    def activate_scenario(self) -> None:
        if self.status is not SimulationStatus.READY:
            raise DomainRuleViolation("Only prepared simulations can activate a scenario.")
        if self.scenario_runtime is None:
            raise DomainRuleViolation("Simulation has no loaded scenario runtime.")
        self.scenario_runtime.activate(self.current_time)

    def suspend_scenario(self) -> None:
        runtime = self._require_scenario_runtime()
        runtime.suspend(self.current_time)

    def resume_scenario(self) -> None:
        runtime = self._require_scenario_runtime()
        runtime.resume(self.current_time)

    def advance_scenario_phase(self) -> None:
        runtime = self._require_scenario_runtime()
        runtime.advance_phase(self.current_time)

    def move_scenario_to_phase(self, phase_name: str) -> None:
        self._require_scenario_runtime().move_to_phase(phase_name, self.current_time)

    def mark_scenario_completion_criterion(self, criterion: str) -> None:
        self._require_scenario_runtime().mark_completion_criterion(criterion)

    def complete_scenario(self) -> None:
        self._require_scenario_runtime().complete(self.current_time)

    def fail_scenario(self) -> None:
        self._require_scenario_runtime().fail(self.current_time)

    def cancel_scenario(self) -> None:
        self._require_scenario_runtime().cancel(self.current_time)

    def load_event_scheduler(self) -> EventScheduler:
        runtime = self._require_scenario_runtime()
        if runtime.status is not ScenarioRuntimeStatus.ACTIVE:
            raise DomainRuleViolation("Event scheduler requires an active scenario runtime.")
        if self.event_scheduler is not None:
            raise DomainRuleViolation("Simulation already has an event scheduler.")
        from .event_scheduler import EventScheduler

        self.event_scheduler = EventScheduler.load(
            self.id,
            runtime.definition.id,
            runtime.definition.scheduled_events,
            self.current_time,
        )
        return self.event_scheduler

    def refresh_scheduled_events(self, state: SchedulerState) -> tuple[EventRuntime, ...]:
        return self._require_event_scheduler().refresh(self, self._require_scenario_runtime(), state)

    def manually_activate_event(self, event_id: UUID, state: SchedulerState) -> EventRuntime:
        return self._require_event_scheduler().manual_activate(
            self,
            self._require_scenario_runtime(),
            event_id,
            state,
        )

    def resolve_scheduled_event(self, event_id: UUID) -> EventRuntime | None:
        return self._require_event_scheduler().resolve(event_id, self.current_time)

    def fail_scheduled_event(self, event_id: UUID) -> None:
        self._require_event_scheduler().fail(event_id, self.current_time)

    def cancel_scheduled_event(self, event_id: UUID) -> None:
        self._require_event_scheduler().cancel(event_id, self.current_time)

    def load_decision_engine(self) -> DecisionEngine:
        runtime = self._require_scenario_runtime()
        if runtime.status is not ScenarioRuntimeStatus.ACTIVE:
            raise DomainRuleViolation("Decision engine requires an active scenario runtime.")
        if self.decision_engine is not None:
            raise DomainRuleViolation("Simulation already has a decision engine.")
        from .decision_engine import DecisionEngine

        self.decision_engine = DecisionEngine(self.id, runtime.definition.id)
        return self.decision_engine

    def create_decision_request(self, request: DecisionRequest) -> object:
        return self._require_decision_engine().create(self, request)

    def open_decision_request(self, request_id: UUID) -> None:
        self._require_decision_engine().open(request_id, self.current_time)

    def submit_decision(self, submission: DecisionSubmission) -> None:
        self._require_decision_engine().submit(self, submission)

    def start_decision_review(self, request_id: UUID) -> None:
        self._require_decision_engine().start_review(request_id, self.current_time)

    def approve_decision(self, request_id: UUID, rationale: str, correlation_id: UUID, causation_id: UUID | None = None) -> DecisionOutcome:
        return self._require_decision_engine().approve(request_id, self.current_time, rationale, correlation_id, causation_id)

    def _require_decision_engine(self) -> DecisionEngine:
        if self.decision_engine is None:
            raise DomainRuleViolation("Simulation has no loaded decision engine.")
        return self.decision_engine
    def _require_event_scheduler(self) -> EventScheduler:
        if self.event_scheduler is None:
            raise DomainRuleViolation("Simulation has no loaded event scheduler.")
        return self.event_scheduler
    def _require_scenario_runtime(self) -> ScenarioRuntime:
        if self.scenario_runtime is None:
            raise DomainRuleViolation("Simulation has no loaded scenario runtime.")
        return self.scenario_runtime

    def _record(self, event: SimulationDomainEvent) -> None:
        self.domain_events = (*self.domain_events, event)
        self.audit_trail = (*self.audit_trail, event)


SimulationSession = Simulation