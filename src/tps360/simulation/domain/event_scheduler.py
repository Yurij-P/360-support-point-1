from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from tps360.core.exceptions import DomainRuleViolation

from .enums import (
    ActivationConditionType,
    DependencyRule,
    EventPriority,
    EventRuntimeStatus,
    ScheduledEventType,
    SimulationStatus,
)
from .events import (
    EventActivated,
    EventBlocked,
    EventCancelled,
    EventExpired,
    EventFailed,
    EventReady,
    EventResolved,
    EventScheduled,
    RecurringEventOccurrenceCreated,
)
from .scenario_runtime import ScenarioRuntime


class SchedulerSimulation(Protocol):
    status: SimulationStatus
    current_time: datetime
from .enums import ScenarioRuntimeStatus, ScenarioValidationLevel
from .scenario_validation import (
    ScenarioValidationMessage,
    ScenarioValidationResult,
)
from .scheduled_event import ActivationCondition, EventParameter, ScheduledEvent


@dataclass(frozen=True)
class SchedulerState:
    """Immutable values available to safe, typed event activation conditions."""

    state_values: tuple[EventParameter, ...] = ()
    active_threat_ids: tuple[UUID, ...] = ()

    def value_for(self, key: str) -> str | int | float | bool | None:
        for parameter in self.state_values:
            if parameter.key == key:
                return parameter.value
        return None


@dataclass
class EventRuntime:
    definition: ScheduledEvent
    occurrence_index: int
    scheduled_time: datetime | None
    status: EventRuntimeStatus = EventRuntimeStatus.SCHEDULED
    audit_trail: tuple[object, ...] = field(default_factory=tuple)

    def __setattr__(self, name: str, value: object) -> None:
        if (
            hasattr(self, "status")
            and self.status
            in {
                EventRuntimeStatus.RESOLVED,
                EventRuntimeStatus.EXPIRED,
                EventRuntimeStatus.CANCELLED,
                EventRuntimeStatus.FAILED,
            }
            and name in {"status", "scheduled_time", "audit_trail"}
        ):
            raise DomainRuleViolation("Final event runtimes cannot be changed.")
        super().__setattr__(name, value)

    @property
    def occurrence_id(self) -> UUID:
        return uuid5(NAMESPACE_URL, f"{self.definition.id}:{self.occurrence_index}")

    def record(self, event: object) -> None:
        self.audit_trail = (*self.audit_trail, event)


@dataclass
class EventScheduler:
    """Deterministic scheduler for immutable scenario event definitions."""

    simulation_id: UUID
    scenario_id: UUID
    event_runtimes: tuple[EventRuntime, ...]
    validation_result: ScenarioValidationResult
    audit_trail: tuple[object, ...] = field(default_factory=tuple)

    @classmethod
    def load(
        cls,
        simulation_id: UUID,
        scenario_id: UUID,
        events: tuple[ScheduledEvent, ...],
        loaded_at: datetime,
    ) -> EventScheduler:
        validation_result = cls.validate_events(scenario_id, events)
        if validation_result.errors:
            raise DomainRuleViolation("Event schedule contains blocking validation errors.")
        runtimes = tuple(
            EventRuntime(definition=event, occurrence_index=0, scheduled_time=event.scheduled_time)
            for event in cls._ordered_definitions(events)
        )
        scheduler = cls(simulation_id, scenario_id, runtimes, validation_result)
        for runtime in scheduler.event_runtimes:
            scheduler._transition(runtime, EventRuntimeStatus.SCHEDULED, loaded_at, "loaded")
        return scheduler

    @staticmethod
    def validate_events(
        scenario_id: UUID,
        events: tuple[ScheduledEvent, ...],
    ) -> ScenarioValidationResult:
        messages: list[ScenarioValidationMessage] = []
        definitions = {event.id: event for event in events}
        if len(definitions) != len(events):
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.ERROR,
                    "duplicate_event_id",
                    "Scheduled event IDs must be unique.",
                )
            )
        for event in events:
            if event.scenario_id != scenario_id:
                messages.append(
                    ScenarioValidationMessage(
                        ScenarioValidationLevel.ERROR,
                        "wrong_scenario_id",
                        "Scheduled event does not belong to the scenario.",
                    )
                )
            for dependency in event.dependencies:
                if dependency.event_id == event.id:
                    messages.append(
                        ScenarioValidationMessage(
                            ScenarioValidationLevel.ERROR,
                            "self_dependency",
                            "An event cannot depend on itself.",
                        )
                    )
                elif dependency.event_id not in definitions:
                    level = (
                        ScenarioValidationLevel.ERROR
                        if dependency.required
                        else ScenarioValidationLevel.WARNING
                    )
                    messages.append(
                        ScenarioValidationMessage(
                            level,
                            "missing_dependency",
                            "A dependency references an event absent from the schedule.",
                        )
                    )
        if EventScheduler._has_cycle(events):
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.ERROR,
                    "cyclic_dependency",
                    "Scheduled event dependencies contain a cycle.",
                )
            )
        messages.append(
            ScenarioValidationMessage(
                ScenarioValidationLevel.INFORMATION,
                "schedule_checked",
                "Event schedule was checked without using system time.",
            )
        )
        return ScenarioValidationResult(tuple(messages))

    def refresh(self, simulation: SchedulerSimulation, runtime: ScenarioRuntime, state: SchedulerState) -> tuple[EventRuntime, ...]:
        self._ensure_running(simulation, runtime)
        activated: list[EventRuntime] = []
        for event_runtime in self._ordered_runtimes():
            if event_runtime.status in self._final_statuses():
                continue
            if self._expire_if_needed(event_runtime, simulation.current_time):
                continue
            if event_runtime.definition.event_type is ScheduledEventType.MANUAL:
                continue
            reason = self._blocking_reason(event_runtime, runtime, state, simulation.current_time)
            if reason is not None:
                self._transition(event_runtime, EventRuntimeStatus.BLOCKED, simulation.current_time, reason)
                continue
            self._transition(event_runtime, EventRuntimeStatus.READY, simulation.current_time, "conditions_met")
            self._transition(event_runtime, EventRuntimeStatus.ACTIVE, simulation.current_time, "automatic_activation")
            activated.append(event_runtime)
        return tuple(activated)

    def manual_activate(self, simulation: SchedulerSimulation, runtime: ScenarioRuntime, event_id: UUID, state: SchedulerState) -> EventRuntime:
        self._ensure_running(simulation, runtime)
        event_runtime = self._require_runtime(event_id)
        if event_runtime.definition.event_type is not ScheduledEventType.MANUAL:
            raise DomainRuleViolation("Only manual events can be manually activated.")
        if event_runtime.status in self._final_statuses():
            raise DomainRuleViolation("Final events cannot be activated.")
        reason = self._blocking_reason(event_runtime, runtime, state, simulation.current_time)
        if reason is not None:
            self._transition(event_runtime, EventRuntimeStatus.BLOCKED, simulation.current_time, reason)
            raise DomainRuleViolation("Manual event conditions are not satisfied.")
        self._transition(event_runtime, EventRuntimeStatus.READY, simulation.current_time, "manual_request")
        self._transition(event_runtime, EventRuntimeStatus.ACTIVE, simulation.current_time, "manual_activation")
        return event_runtime

    def resolve(self, event_id: UUID, occurred_at: datetime) -> EventRuntime | None:
        runtime = self._require_runtime(event_id)
        if runtime.status is not EventRuntimeStatus.ACTIVE:
            raise DomainRuleViolation("Only active events can be resolved.")
        self._transition(runtime, EventRuntimeStatus.RESOLVED, occurred_at, "resolved")
        return self._create_recurrence(runtime, occurred_at)

    def fail(self, event_id: UUID, occurred_at: datetime) -> None:
        runtime = self._require_runtime(event_id)
        if runtime.status is not EventRuntimeStatus.ACTIVE:
            raise DomainRuleViolation("Only active events can fail.")
        self._transition(runtime, EventRuntimeStatus.FAILED, occurred_at, "failed")

    def cancel(self, event_id: UUID, occurred_at: datetime) -> None:
        runtime = self._require_runtime(event_id)
        if runtime.status in self._final_statuses():
            raise DomainRuleViolation("Final events cannot be cancelled.")
        self._transition(runtime, EventRuntimeStatus.CANCELLED, occurred_at, "cancelled")

    def _blocking_reason(
        self,
        event_runtime: EventRuntime,
        scenario_runtime: ScenarioRuntime,
        state: SchedulerState,
        current_time: datetime,
    ) -> str | None:
        definition = event_runtime.definition
        if event_runtime.scheduled_time is not None and current_time < event_runtime.scheduled_time:
            return "scheduled_time_not_reached"
        if definition.scenario_phase is not None and scenario_runtime.current_phase != definition.scenario_phase:
            return "scenario_phase_not_active"
        if not self._dependencies_satisfied(definition):
            return "dependencies_not_satisfied"
        if not all(self._condition_satisfied(condition, scenario_runtime, state) for condition in definition.activation_conditions):
            return "activation_conditions_not_satisfied"
        return None

    def _dependencies_satisfied(self, definition: ScheduledEvent) -> bool:
        dependency_statuses: list[bool] = []
        for dependency in definition.dependencies:
            matching = [runtime for runtime in self.event_runtimes if runtime.definition.id == dependency.event_id]
            if not matching:
                if dependency.required:
                    return False
                continue
            dependency_statuses.append(any(runtime.status is EventRuntimeStatus.RESOLVED for runtime in matching))
        if not dependency_statuses:
            return True
        if definition.dependency_rule is DependencyRule.ALL:
            return all(dependency_statuses)
        return any(dependency_statuses)

    def _condition_satisfied(
        self,
        condition: ActivationCondition,
        runtime: ScenarioRuntime,
        state: SchedulerState,
    ) -> bool:
        if condition.condition_type is ActivationConditionType.PHASE_IS:
            return runtime.current_phase == condition.expected_value
        if condition.condition_type is ActivationConditionType.EVENT_STATUS_IS:
            return any(
                event_runtime.definition.id == condition.event_id
                and event_runtime.status is condition.expected_event_status
                for event_runtime in self.event_runtimes
            )
        if condition.condition_type is ActivationConditionType.STATE_VALUE_EQUALS:
            return state.value_for(condition.key) == condition.expected_value
        if condition.condition_type is ActivationConditionType.ACTIVE_THREAT_PRESENT:
            return condition.key in {str(threat_id) for threat_id in state.active_threat_ids}
        if condition.condition_type is ActivationConditionType.TERRITORY_AVAILABLE:
            return condition.key in runtime.definition.required_territories
        if condition.condition_type is ActivationConditionType.INFRASTRUCTURE_AVAILABLE:
            return condition.key in runtime.definition.required_infrastructure
        if condition.condition_type is ActivationConditionType.RESOURCE_AVAILABLE:
            return condition.key in {str(resource_id) for resource_id in runtime.definition.required_resource_ids}
        return False

    def _expire_if_needed(self, runtime: EventRuntime, current_time: datetime) -> bool:
        if runtime.definition.expires_at is None or current_time <= runtime.definition.expires_at:
            return False
        if runtime.status in {EventRuntimeStatus.SCHEDULED, EventRuntimeStatus.BLOCKED}:
            self._transition(runtime, EventRuntimeStatus.EXPIRED, current_time, "time_window_expired")
            return True
        return False

    def _create_recurrence(self, runtime: EventRuntime, occurred_at: datetime) -> EventRuntime | None:
        definition = runtime.definition
        if (
            definition.event_type is not ScheduledEventType.RECURRING
            or runtime.occurrence_index >= definition.repeat_count
            or definition.recurrence_interval_minutes is None
            or runtime.scheduled_time is None
        ):
            return None
        next_runtime = EventRuntime(
            definition=definition,
            occurrence_index=runtime.occurrence_index + 1,
            scheduled_time=runtime.scheduled_time
            + timedelta(minutes=definition.recurrence_interval_minutes),
        )
        self.event_runtimes = (*self.event_runtimes, next_runtime)
        event = RecurringEventOccurrenceCreated(
            self.simulation_id,
            self.scenario_id,
            definition.id,
            definition.version,
            next_runtime.occurrence_index,
            occurred_at,
            "recurrence_created",
        )
        next_runtime.record(event)
        self.audit_trail = (*self.audit_trail, event)
        self._transition(next_runtime, EventRuntimeStatus.SCHEDULED, occurred_at, "recurrence_scheduled")
        return next_runtime

    def _transition(
        self,
        runtime: EventRuntime,
        target: EventRuntimeStatus,
        occurred_at: datetime,
        reason: str,
    ) -> None:
        if runtime.status is target and target not in {EventRuntimeStatus.BLOCKED, EventRuntimeStatus.SCHEDULED}:
            return
        event = self._event_for(runtime, target, occurred_at, reason)
        runtime.record(event)
        self.audit_trail = (*self.audit_trail, event)
        runtime.status = target

    def _event_for(self, runtime: EventRuntime, target: EventRuntimeStatus, occurred_at: datetime, reason: str) -> object:
        args = (
            self.simulation_id,
            self.scenario_id,
            runtime.definition.id,
            runtime.definition.version,
            runtime.occurrence_index,
            occurred_at,
            reason,
        )
        event_types = {
            EventRuntimeStatus.SCHEDULED: EventScheduled,
            EventRuntimeStatus.BLOCKED: EventBlocked,
            EventRuntimeStatus.READY: EventReady,
            EventRuntimeStatus.ACTIVE: EventActivated,
            EventRuntimeStatus.RESOLVED: EventResolved,
            EventRuntimeStatus.FAILED: EventFailed,
            EventRuntimeStatus.EXPIRED: EventExpired,
            EventRuntimeStatus.CANCELLED: EventCancelled,
        }
        return event_types[target](*args)

    def _require_runtime(self, event_id: UUID) -> EventRuntime:
        for runtime in self.event_runtimes:
            if runtime.definition.id == event_id and runtime.status not in self._final_statuses():
                return runtime
        raise DomainRuleViolation("Event runtime is unavailable.")

    def _ensure_running(self, simulation: SchedulerSimulation, runtime: ScenarioRuntime) -> None:
        if simulation.status is not SimulationStatus.RUNNING:
            raise DomainRuleViolation("Event scheduler runs only in running simulations.")
        if runtime.status is not ScenarioRuntimeStatus.ACTIVE:
            raise DomainRuleViolation("Event scheduler requires an active scenario runtime.")

    def _ordered_runtimes(self) -> tuple[EventRuntime, ...]:
        return tuple(
            sorted(
                self.event_runtimes,
                key=lambda runtime: (
                    runtime.scheduled_time or datetime.max,
                    self._priority_rank(runtime.definition.priority),
                    str(runtime.definition.id),
                    runtime.occurrence_index,
                ),
            )
        )

    @staticmethod
    def _ordered_definitions(events: tuple[ScheduledEvent, ...]) -> tuple[ScheduledEvent, ...]:
        return tuple(
            sorted(
                events,
                key=lambda event: (
                    event.scheduled_time or datetime.max,
                    EventScheduler._priority_rank(event.priority),
                    str(event.id),
                ),
            )
        )

    @staticmethod
    def _priority_rank(priority: EventPriority) -> int:
        return {
            EventPriority.CRITICAL: 0,
            EventPriority.HIGH: 1,
            EventPriority.NORMAL: 2,
            EventPriority.LOW: 3,
        }[priority]

    @staticmethod
    def _final_statuses() -> set[EventRuntimeStatus]:
        return {
            EventRuntimeStatus.RESOLVED,
            EventRuntimeStatus.EXPIRED,
            EventRuntimeStatus.CANCELLED,
            EventRuntimeStatus.FAILED,
        }

    @staticmethod
    def _has_cycle(events: tuple[ScheduledEvent, ...]) -> bool:
        graph = {event.id: tuple(dependency.event_id for dependency in event.dependencies) for event in events}
        visiting: set[UUID] = set()
        visited: set[UUID] = set()

        def visit(event_id: UUID) -> bool:
            if event_id in visiting:
                return True
            if event_id in visited or event_id not in graph:
                return False
            visiting.add(event_id)
            cyclic = any(visit(dependency_id) for dependency_id in graph[event_id])
            visiting.remove(event_id)
            visited.add(event_id)
            return cyclic

        return any(visit(event_id) for event_id in graph)