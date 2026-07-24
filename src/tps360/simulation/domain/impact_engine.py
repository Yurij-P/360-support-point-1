from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import isfinite
from typing import TYPE_CHECKING
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation

from .enums import (
    EventRuntimeStatus,
    ImpactCategory,
    ImpactConflictPolicy,
    ImpactOperation,
    ImpactSourceType,
    ImpactStatus,
    ImpactTargetType,
    ScenarioRuntimeStatus,
    ScenarioValidationLevel,
    SimulationStatus,
)
from .simulation_state import SimulationState, StateKey, StateValue

if TYPE_CHECKING:
    from .simulation import Simulation


@dataclass(frozen=True)
class ImpactTarget:
    target_type: ImpactTargetType
    target_id: UUID | None
    field: str

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise DomainRuleViolation("Impact target field must not be empty.")

    @property
    def state_key(self) -> StateKey:
        return StateKey(self.target_type, self.target_id, self.field)


@dataclass(frozen=True)
class ImpactCondition:
    """Safe typed condition; no callbacks or executable expressions."""

    target: ImpactTarget
    expected_value: float | bool


@dataclass(frozen=True)
class ImpactChange:
    target: ImpactTarget
    operation: ImpactOperation
    value: float | bool
    unit: str
    required: bool = True
    minimum: float | None = 0.0
    maximum: float | None = None

    def __post_init__(self) -> None:
        if not self.unit.strip():
            raise DomainRuleViolation("Impact change unit must not be empty.")
        if isinstance(self.value, float) and not isfinite(self.value):
            raise DomainRuleViolation("Impact change value must be finite.")
        numeric = {ImpactOperation.SET, ImpactOperation.INCREASE, ImpactOperation.DECREASE, ImpactOperation.MULTIPLY, ImpactOperation.DAMAGE, ImpactOperation.RESTORE, ImpactOperation.CONSUME, ImpactOperation.REPLENISH}
        if self.operation in numeric and (isinstance(self.value, bool) or not isinstance(self.value, (int, float))):
            raise DomainRuleViolation("Numeric impact operations require a numeric value.")
        boolean = {ImpactOperation.ACTIVATE, ImpactOperation.DEACTIVATE, ImpactOperation.LOCK, ImpactOperation.UNLOCK}
        if self.operation in boolean and not isinstance(self.value, bool):
            raise DomainRuleViolation("State-toggle impact operations require a boolean value.")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise DomainRuleViolation("Impact minimum cannot exceed maximum.")


@dataclass(frozen=True)
class ImpactDependency:
    impact_id: UUID
    required: bool = True


@dataclass(frozen=True)
class ImpactDefinition:
    id: UUID
    scenario_id: UUID
    source_type: ImpactSourceType
    source_id: UUID | None
    name: str
    description: str
    category: ImpactCategory
    changes: tuple[ImpactChange, ...]
    delay_minutes: int
    duration_minutes: int | None
    temporary: bool
    conditions: tuple[ImpactCondition, ...] = ()
    priority: int = 0
    conflict_policy: ImpactConflictPolicy = ImpactConflictPolicy.SEQUENTIAL
    dependencies: tuple[ImpactDependency, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.description.strip():
            raise DomainRuleViolation("Impact definition name and description must not be empty.")
        if not self.changes:
            raise DomainRuleViolation("Impact definition requires at least one change.")
        if self.delay_minutes < 0 or self.duration_minutes is not None and self.duration_minutes <= 0:
            raise DomainRuleViolation("Impact timing values are invalid.")
        if self.temporary != (self.duration_minutes is not None):
            raise DomainRuleViolation("Temporary impacts require a duration and permanent impacts cannot have one.")
        if self.version < 1:
            raise DomainRuleViolation("Impact definition version must be at least one.")
        if len({dependency.impact_id for dependency in self.dependencies}) != len(self.dependencies):
            raise DomainRuleViolation("Impact dependencies must be unique.")
        if any(dependency.impact_id == self.id for dependency in self.dependencies):
            raise DomainRuleViolation("An impact cannot depend on itself.")
        if len({key for key, _ in self.metadata}) != len(self.metadata) or any(not key.strip() for key, _ in self.metadata):
            raise DomainRuleViolation("Impact metadata keys must be non-empty and unique.")


@dataclass(frozen=True)
class ImpactValidationResult:
    messages: tuple[tuple[ScenarioValidationLevel, str, str], ...]

    @property
    def errors(self) -> tuple[tuple[ScenarioValidationLevel, str, str], ...]:
        return tuple(message for message in self.messages if message[0] is ScenarioValidationLevel.ERROR)

    @property
    def warnings(self) -> tuple[tuple[ScenarioValidationLevel, str, str], ...]:
        return tuple(message for message in self.messages if message[0] is ScenarioValidationLevel.WARNING)

    @property
    def information(self) -> tuple[tuple[ScenarioValidationLevel, str, str], ...]:
        return tuple(message for message in self.messages if message[0] is ScenarioValidationLevel.INFORMATION)


@dataclass(frozen=True)
class AppliedChange:
    target: ImpactTarget
    previous_value: float | bool | None
    new_value: float | bool
    operation: ImpactOperation


@dataclass(frozen=True)
class ImpactResult:
    instance_id: UUID
    simulation_id: UUID
    scenario_id: UUID
    source_id: UUID | None
    status: ImpactStatus
    applied_changes: tuple[AppliedChange, ...]
    skipped_changes: tuple[ImpactChange, ...]
    reasons: tuple[str, ...]
    occurred_at: datetime
    state_version_before: int
    state_version_after: int
    correlation_id: UUID
    causation_id: UUID | None


@dataclass
class ImpactInstance:
    id: UUID
    definition: ImpactDefinition
    simulation_id: UUID
    scheduled_at: datetime
    correlation_id: UUID
    causation_id: UUID | None
    status: ImpactStatus = ImpactStatus.PENDING
    result: ImpactResult | None = None
    applied_changes: tuple[AppliedChange, ...] = ()
    audit_trail: tuple[object, ...] = field(default_factory=tuple)

    def __setattr__(self, name: str, value: object) -> None:
        if hasattr(self, "status") and self.status in {ImpactStatus.REVERSED, ImpactStatus.EXPIRED, ImpactStatus.CANCELLED, ImpactStatus.FAILED} and name in {"status", "result", "applied_changes", "audit_trail"}:
            raise DomainRuleViolation("Final impact instances cannot be changed.")
        super().__setattr__(name, value)


@dataclass
class ImpactEngine:
    simulation_id: UUID
    scenario_id: UUID
    instances: tuple[ImpactInstance, ...] = ()
    audit_trail: tuple[object, ...] = field(default_factory=tuple)

    def create(self, simulation: Simulation, instance_id: UUID, definition: ImpactDefinition, correlation_id: UUID, causation_id: UUID | None = None) -> ImpactInstance:
        self._ensure_running(simulation)
        if definition.scenario_id != self.scenario_id:
            raise DomainRuleViolation("Impact definition does not belong to this scenario.")
        self._validate_source(simulation, definition)
        if any(item.id == instance_id for item in self.instances):
            raise DomainRuleViolation("Impact instance ID already exists.")
        instance = ImpactInstance(instance_id, definition, self.simulation_id, simulation.current_time + timedelta(minutes=definition.delay_minutes), correlation_id, causation_id)
        instance.status = ImpactStatus.SCHEDULED if definition.delay_minutes else ImpactStatus.READY
        self.instances = (*self.instances, instance)
        self._record(instance, ("ImpactCreated", simulation.current_time))
        self._record(instance, ("ImpactScheduled" if definition.delay_minutes else "ImpactReady", simulation.current_time))
        return instance

    def refresh(self, simulation: Simulation) -> tuple[ImpactResult, ...]:
        self._ensure_running(simulation)
        results: list[ImpactResult] = []
        for instance in self._ordered():
            if instance.status is ImpactStatus.SCHEDULED and simulation.current_time >= instance.scheduled_at:
                instance.status = ImpactStatus.READY
                self._record(instance, ("ImpactReady", simulation.current_time))
            if instance.status is ImpactStatus.READY:
                results.append(self.apply(simulation, instance.id))
            elif instance.status is ImpactStatus.ACTIVE and instance.definition.duration_minutes is not None and simulation.current_time >= instance.scheduled_at + timedelta(minutes=instance.definition.duration_minutes):
                self.reverse(simulation, instance.id)
        return tuple(results)

    def apply(self, simulation: Simulation, instance_id: UUID) -> ImpactResult:
        self._ensure_running(simulation)
        instance = self._instance(instance_id)
        if instance.status is ImpactStatus.SCHEDULED:
            raise DomainRuleViolation("Impact cannot be applied before its scheduled simulation time.")
        if instance.status is not ImpactStatus.READY:
            raise DomainRuleViolation("Only ready impacts can be applied.")
        if not self._conditions_match(simulation.state, instance.definition.conditions):
            instance.status = ImpactStatus.FAILED
            raise DomainRuleViolation("Impact conditions are not satisfied.")
        before = simulation.state
        try:
            changes, skipped, values = self._calculate(before, instance.definition.changes)
        except DomainRuleViolation:
            instance.status = ImpactStatus.FAILED
            raise
        after = before.with_values(values)
        simulation.replace_simulation_state(after)
        result = ImpactResult(instance.id, self.simulation_id, self.scenario_id, instance.definition.source_id, ImpactStatus.APPLIED, changes, skipped, (), simulation.current_time, before.version, after.version, instance.correlation_id, instance.causation_id)
        instance.applied_changes = changes
        instance.result = result
        instance.status = ImpactStatus.ACTIVE if instance.definition.temporary else ImpactStatus.APPLIED
        self._record(instance, ("ImpactApplied", simulation.current_time, before.version, after.version))
        return result

    def reverse(self, simulation: Simulation, instance_id: UUID) -> None:
        self._ensure_running(simulation)
        instance = self._instance(instance_id)
        if instance.status is not ImpactStatus.ACTIVE:
            raise DomainRuleViolation("Only active temporary impacts can be reversed.")
        before = simulation.state
        inverse: list[ImpactChange] = []
        for change in instance.applied_changes:
            operation = {ImpactOperation.INCREASE: ImpactOperation.DECREASE, ImpactOperation.DECREASE: ImpactOperation.INCREASE, ImpactOperation.CONSUME: ImpactOperation.REPLENISH, ImpactOperation.REPLENISH: ImpactOperation.CONSUME, ImpactOperation.DAMAGE: ImpactOperation.RESTORE, ImpactOperation.RESTORE: ImpactOperation.DAMAGE}.get(change.operation)
            if operation is None or not isinstance(change.new_value, (int, float)) or isinstance(change.new_value, bool):
                instance.status = ImpactStatus.FAILED
                raise DomainRuleViolation("Impact cannot be safely reversed automatically.")
            inverse.append(ImpactChange(change.target, operation, abs(float(change.new_value) - float(change.previous_value or 0)), "reversal"))
        _, _, values = self._calculate(before, tuple(inverse))
        simulation.replace_simulation_state(before.with_values(values))
        self._record(instance, ("ImpactReversed", simulation.current_time))
        instance.status = ImpactStatus.REVERSED

    def cancel(self, instance_id: UUID, occurred_at: datetime) -> None:
        instance = self._instance(instance_id)
        if instance.status in {ImpactStatus.APPLIED, ImpactStatus.REVERSED, ImpactStatus.EXPIRED, ImpactStatus.CANCELLED, ImpactStatus.FAILED}:
            raise DomainRuleViolation("Final impacts cannot be cancelled.")
        self._record(instance, ("ImpactCancelled", occurred_at))
        instance.status = ImpactStatus.CANCELLED

    def _calculate(self, state: SimulationState, definitions: tuple[ImpactChange, ...]) -> tuple[tuple[AppliedChange, ...], tuple[ImpactChange, ...], tuple[StateValue, ...]]:
        mapping = {item.key: item.value for item in state.values}
        applied: list[AppliedChange] = []; skipped: list[ImpactChange] = []
        for change in definitions:
            try:
                key = change.target.state_key; previous = mapping.get(key)
                new = self._operate(previous, change)
                if isinstance(new, float) and not isfinite(new): raise DomainRuleViolation("Impact result must be finite.")
                if isinstance(new, (int, float)) and not isinstance(new, bool) and change.minimum is not None and new < change.minimum: raise DomainRuleViolation("Impact result is below its minimum.")
                if isinstance(new, (int, float)) and not isinstance(new, bool) and change.maximum is not None and new > change.maximum: raise DomainRuleViolation("Impact result exceeds its maximum.")
                mapping[key] = new; applied.append(AppliedChange(change.target, previous, new, change.operation))
            except DomainRuleViolation:
                if change.required: raise
                skipped.append(change)
        return tuple(applied), tuple(skipped), tuple(sorted((StateValue(key, value) for key, value in mapping.items()), key=lambda item: (item.key.target_type.value, str(item.key.target_id), item.key.field)))

    @staticmethod
    def _operate(previous: float | bool | None, change: ImpactChange) -> float | bool:
        number = 0.0 if previous is None else previous
        if change.operation is ImpactOperation.SET: return float(change.value)
        if change.operation in {ImpactOperation.ACTIVATE, ImpactOperation.UNLOCK}: return True
        if change.operation in {ImpactOperation.DEACTIVATE, ImpactOperation.LOCK}: return False
        if isinstance(number, bool): raise DomainRuleViolation("Numeric impact cannot modify boolean state.")
        value = float(change.value)
        if change.operation in {ImpactOperation.INCREASE, ImpactOperation.RESTORE, ImpactOperation.REPLENISH}: return float(number) + value
        if change.operation in {ImpactOperation.DECREASE, ImpactOperation.DAMAGE, ImpactOperation.CONSUME}: return float(number) - value
        if change.operation is ImpactOperation.MULTIPLY: return float(number) * value
        raise DomainRuleViolation("Unsupported impact operation.")

    def _validate_source(self, simulation: Simulation, definition: ImpactDefinition) -> None:
        if definition.source_type is ImpactSourceType.SYSTEM:
            if definition.source_id is None: raise DomainRuleViolation("System impacts require an explicit source ID.")
            return
        if definition.source_id is None: raise DomainRuleViolation("Impact source ID is required.")
        if definition.source_type in {ImpactSourceType.EVENT, ImpactSourceType.COMBINED}:
            scheduler = simulation.event_scheduler
            if scheduler is None or not any(item.definition.id == definition.source_id and item.status in {EventRuntimeStatus.ACTIVE, EventRuntimeStatus.RESOLVED} for item in scheduler.event_runtimes):
                raise DomainRuleViolation("Impact event source is not active in this simulation.")
        if definition.source_type in {ImpactSourceType.DECISION, ImpactSourceType.COMBINED}:
            engine = simulation.decision_engine
            if engine is None or not any(item.request.id == definition.source_id and item.outcome is not None for item in engine.runtimes):
                raise DomainRuleViolation("Impact decision source is not approved in this simulation.")

    @staticmethod
    def _conditions_match(state: SimulationState, conditions: tuple[ImpactCondition, ...]) -> bool:
        return all(state.get(condition.target.state_key) == condition.expected_value for condition in conditions)

    def _ensure_running(self, simulation: Simulation) -> None:
        if simulation.id != self.simulation_id or simulation.status is not SimulationStatus.RUNNING:
            raise DomainRuleViolation("Impact engine runs only in its running simulation.")
        if simulation.scenario_runtime is None or simulation.scenario_runtime.status is not ScenarioRuntimeStatus.ACTIVE:
            raise DomainRuleViolation("Impact engine requires an active scenario runtime.")

    def _instance(self, instance_id: UUID) -> ImpactInstance:
        for item in self.instances:
            if item.id == instance_id: return item
        raise DomainRuleViolation("Impact instance is unavailable.")

    def _ordered(self) -> tuple[ImpactInstance, ...]:
        return tuple(sorted(self.instances, key=lambda item: (item.scheduled_at, -item.definition.priority, str(item.id))))

    def _record(self, instance: ImpactInstance, event: object) -> None:
        instance.audit_trail = (*instance.audit_trail, event)
        self.audit_trail = (*self.audit_trail, event)