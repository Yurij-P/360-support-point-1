from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation

from .enums import ScenarioRuntimeStatus
from .events import (
    ScenarioActivated,
    ScenarioCancelled,
    ScenarioCompleted,
    ScenarioDomainEvent,
    ScenarioFailed,
    ScenarioLoaded,
    ScenarioPhaseChanged,
    ScenarioResumed,
    ScenarioSuspended,
    ScenarioValidated,
)
from .scenario_definition import ScenarioDefinition
from .scenario_validation import ScenarioValidationResult


@dataclass
class ScenarioRuntime:
    """Mutable runtime state for one immutable scenario definition in one simulation."""

    simulation_id: UUID
    definition: ScenarioDefinition
    status: ScenarioRuntimeStatus = ScenarioRuntimeStatus.LOADED
    validation_result: ScenarioValidationResult | None = None
    activated_at: datetime | None = None
    current_phase_index: int | None = None
    active_goal_ids: tuple[UUID, ...] = ()
    active_conditions: tuple[str, ...] = ()
    met_completion_criteria: tuple[str, ...] = ()
    domain_events: tuple[ScenarioDomainEvent, ...] = field(default_factory=tuple)
    audit_trail: tuple[ScenarioDomainEvent, ...] = field(default_factory=tuple)

    @classmethod
    def load(
        cls,
        simulation_id: UUID,
        definition: ScenarioDefinition,
        loaded_at: datetime,
    ) -> ScenarioRuntime:
        runtime = cls(simulation_id=simulation_id, definition=definition)
        runtime._record(ScenarioLoaded(simulation_id, definition.id, definition.version, loaded_at))
        return runtime

    @property
    def current_phase(self) -> str | None:
        if self.current_phase_index is None:
            return None
        return self.definition.phases[self.current_phase_index].name

    def validate(self, result: ScenarioValidationResult, occurred_at: datetime) -> None:
        self._ensure_status(ScenarioRuntimeStatus.LOADED, "Only loaded scenarios can be validated.")
        self.validation_result = result
        self.status = ScenarioRuntimeStatus.VALIDATED
        self._record(
            ScenarioValidated(
                self.simulation_id,
                self.definition.id,
                self.definition.version,
                occurred_at,
                error_count=len(result.errors),
                warning_count=len(result.warnings),
            )
        )

    def activate(self, occurred_at: datetime) -> None:
        self._ensure_status(ScenarioRuntimeStatus.VALIDATED, "Only validated scenarios can be activated.")
        if self.validation_result is None or not self.validation_result.can_activate:
            raise DomainRuleViolation("A scenario with validation errors cannot be activated.")
        self.status = ScenarioRuntimeStatus.ACTIVE
        self.activated_at = occurred_at
        self.active_goal_ids = tuple(goal.id for goal in self.definition.simulation_goals)
        self.active_conditions = self.definition.initial_conditions
        self._record(
            ScenarioActivated(self.simulation_id, self.definition.id, self.definition.version, occurred_at)
        )
        if self.definition.phases:
            self._change_phase(0, occurred_at)

    def suspend(self, occurred_at: datetime) -> None:
        self._ensure_status(ScenarioRuntimeStatus.ACTIVE, "Only active scenarios can be suspended.")
        self.status = ScenarioRuntimeStatus.SUSPENDED
        self._record(
            ScenarioSuspended(self.simulation_id, self.definition.id, self.definition.version, occurred_at)
        )

    def resume(self, occurred_at: datetime) -> None:
        self._ensure_status(ScenarioRuntimeStatus.SUSPENDED, "Only suspended scenarios can be resumed.")
        self.status = ScenarioRuntimeStatus.ACTIVE
        self._record(
            ScenarioResumed(self.simulation_id, self.definition.id, self.definition.version, occurred_at)
        )

    def advance_phase(self, occurred_at: datetime) -> None:
        self._ensure_status(ScenarioRuntimeStatus.ACTIVE, "Only active scenarios can change phase.")
        if self.current_phase_index is None:
            raise DomainRuleViolation("An active scenario has no configured phase.")
        next_index = self.current_phase_index + 1
        if next_index >= len(self.definition.phases):
            raise DomainRuleViolation("Scenario has no next phase.")
        self._change_phase(next_index, occurred_at)

    def move_to_phase(self, phase_name: str, occurred_at: datetime) -> None:
        self._ensure_status(ScenarioRuntimeStatus.ACTIVE, "Only active scenarios can change phase.")
        target_index = next(
            (
                index
                for index, phase in enumerate(self.definition.phases)
                if phase.name == phase_name
            ),
            None,
        )
        if target_index is None:
            raise DomainRuleViolation("Scenario phase is not defined.")
        expected_index = 0 if self.current_phase_index is None else self.current_phase_index + 1
        if target_index != expected_index:
            raise DomainRuleViolation("Scenario phases must be completed sequentially.")
        self._change_phase(target_index, occurred_at)

    def mark_completion_criterion(self, criterion: str) -> None:
        if self.status not in {ScenarioRuntimeStatus.ACTIVE, ScenarioRuntimeStatus.SUSPENDED}:
            raise DomainRuleViolation("Only active or suspended scenarios can update completion criteria.")
        if criterion not in self.definition.completion_criteria:
            raise DomainRuleViolation("Completion criterion is not defined by the scenario.")
        if criterion not in self.met_completion_criteria:
            self.met_completion_criteria = (*self.met_completion_criteria, criterion)

    def complete(self, occurred_at: datetime) -> None:
        if self.status not in {ScenarioRuntimeStatus.ACTIVE, ScenarioRuntimeStatus.SUSPENDED}:
            raise DomainRuleViolation("Only active or suspended scenarios can be completed.")
        if set(self.met_completion_criteria) != set(self.definition.completion_criteria):
            raise DomainRuleViolation("Scenario completion criteria are not met.")
        self._record(
            ScenarioCompleted(self.simulation_id, self.definition.id, self.definition.version, occurred_at)
        )
        self.status = ScenarioRuntimeStatus.COMPLETED

    def fail(self, occurred_at: datetime) -> None:
        if self.status not in {ScenarioRuntimeStatus.ACTIVE, ScenarioRuntimeStatus.SUSPENDED}:
            raise DomainRuleViolation("Only active or suspended scenarios can fail.")
        self._record(ScenarioFailed(self.simulation_id, self.definition.id, self.definition.version, occurred_at))
        self.status = ScenarioRuntimeStatus.FAILED

    def cancel(self, occurred_at: datetime) -> None:
        if self.status in {
            ScenarioRuntimeStatus.COMPLETED,
            ScenarioRuntimeStatus.FAILED,
            ScenarioRuntimeStatus.CANCELLED,
        }:
            raise DomainRuleViolation("Final scenarios cannot be cancelled.")
        self._record(
            ScenarioCancelled(self.simulation_id, self.definition.id, self.definition.version, occurred_at)
        )
        self.status = ScenarioRuntimeStatus.CANCELLED

    def _change_phase(self, target_index: int, occurred_at: datetime) -> None:
        previous_phase = self.current_phase
        self.current_phase_index = target_index
        self._record(
            ScenarioPhaseChanged(
                self.simulation_id,
                self.definition.id,
                self.definition.version,
                occurred_at,
                previous_phase=previous_phase,
                current_phase=self.current_phase or "",
            )
        )

    def __setattr__(self, name: str, value: object) -> None:
        if (
            hasattr(self, "status")
            and self.status
            in {
                ScenarioRuntimeStatus.COMPLETED,
                ScenarioRuntimeStatus.FAILED,
                ScenarioRuntimeStatus.CANCELLED,
            }
            and name
            in {
                "status",
                "validation_result",
                "activated_at",
                "current_phase_index",
                "active_goal_ids",
                "active_conditions",
                "met_completion_criteria",
                "domain_events",
                "audit_trail",
            }
        ):
            raise DomainRuleViolation("Final scenario runtimes cannot be changed.")
        super().__setattr__(name, value)

    def _ensure_status(self, expected: ScenarioRuntimeStatus, message: str) -> None:
        if self.status is not expected:
            raise DomainRuleViolation(message)

    def _record(self, event: ScenarioDomainEvent) -> None:
        self.domain_events = (*self.domain_events, event)
        self.audit_trail = (*self.audit_trail, event)