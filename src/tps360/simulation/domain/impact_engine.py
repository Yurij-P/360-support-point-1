from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from math import isfinite
from typing import TYPE_CHECKING
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation

from .enums import ImpactCategory, ImpactOperation, ImpactStatus
from .events import (
    ImpactApplied,
    ImpactCancelled,
    ImpactCreated,
    ImpactFailed,
    ImpactReady,
    ImpactScheduled,
    SimulationStateChanged,
)
from .impact_contracts import (
    ImpactDefinitionId,
    ImpactInstanceId,
    ImpactSourceReference,
    TypedImpactTarget,
)
from .simulation_state import SimulationState, StateValue

if TYPE_CHECKING:
    from .simulation import Simulation


@dataclass(frozen=True)
class ImpactCondition:
    target: TypedImpactTarget
    expected_value: float | bool


@dataclass(frozen=True)
class ImpactChange:
    target: TypedImpactTarget
    operation: ImpactOperation
    value: float | bool
    unit: str
    required: bool = True
    minimum: float | None = 0.0
    maximum: float | None = None

    def __post_init__(self) -> None:
        numeric = {ImpactOperation.SET, ImpactOperation.INCREASE, ImpactOperation.DECREASE, ImpactOperation.ADD, ImpactOperation.SUBTRACT, ImpactOperation.MULTIPLY, ImpactOperation.DIVIDE, ImpactOperation.MIN, ImpactOperation.MAX, ImpactOperation.DAMAGE, ImpactOperation.RESTORE, ImpactOperation.CONSUME, ImpactOperation.REPLENISH}
        boolean = {ImpactOperation.ACTIVATE, ImpactOperation.DEACTIVATE, ImpactOperation.LOCK, ImpactOperation.UNLOCK}
        if not self.unit.strip() or (isinstance(self.value, float) and not isfinite(self.value)):
            raise DomainRuleViolation("Impact change unit and value must be valid.")
        if self.operation in numeric and (isinstance(self.value, bool) or not isinstance(self.value, (float, int))):
            raise DomainRuleViolation("Numeric operation requires numeric value.")
        if self.operation in boolean and not isinstance(self.value, bool):
            raise DomainRuleViolation("Toggle operation requires boolean value.")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise DomainRuleViolation("Impact bounds are invalid.")
        if self.operation in boolean and self.target.attribute.value not in {"status"}:
            raise DomainRuleViolation("Toggle operation requires status attribute.")
        if self.operation is ImpactOperation.MULTIPLY and self.target.attribute.value in {"status", "damage"}:
            raise DomainRuleViolation("Multiply is incompatible with this attribute.")


@dataclass(frozen=True)
class SkippedChange:
    change: ImpactChange
    reason: str


@dataclass(frozen=True)
class ImpactDefinition:
    id: ImpactDefinitionId
    scenario_id: UUID
    source: ImpactSourceReference
    name: str
    description: str
    category: ImpactCategory
    changes: tuple[ImpactChange, ...]
    delay_minutes: int = 0
    duration_minutes: int | None = None
    temporary: bool = False
    conditions: tuple[ImpactCondition, ...] = ()
    priority: int = 0
    version: int = 1

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.description.strip() or not self.changes:
            raise DomainRuleViolation("Impact definition requires name, description and changes.")
        if self.source.scenario_id != self.scenario_id or self.delay_minutes < 0 or self.version < 1:
            raise DomainRuleViolation("Impact definition scope, delay or version is invalid.")
        if self.temporary != (self.duration_minutes is not None) or self.duration_minutes is not None and self.duration_minutes <= 0:
            raise DomainRuleViolation("Temporary impact duration is invalid.")
        if any(c.target.session_id != self.source.session_id or c.target.scenario_id != self.scenario_id for c in self.changes):
            raise DomainRuleViolation("Impact change target scope is invalid.")


@dataclass(frozen=True)
class AppliedChange:
    target: TypedImpactTarget
    previous_value: float | bool | None
    new_value: float | bool
    operation: ImpactOperation


@dataclass(frozen=True)
class ImpactResult:
    instance_id: ImpactInstanceId
    simulation_id: UUID
    scenario_id: UUID
    source: ImpactSourceReference
    status: ImpactStatus
    applied_changes: tuple[AppliedChange, ...]
    skipped_changes: tuple[SkippedChange, ...]
    reasons: tuple[str, ...]
    occurred_at: datetime
    state_version_before: int
    state_version_after: int
    correlation_id: UUID
    causation_id: UUID | None


_TRANSITIONS = {ImpactStatus.PENDING: {ImpactStatus.SCHEDULED, ImpactStatus.READY, ImpactStatus.CANCELLED}, ImpactStatus.SCHEDULED: {ImpactStatus.READY, ImpactStatus.CANCELLED}, ImpactStatus.READY: {ImpactStatus.APPLIED, ImpactStatus.FAILED, ImpactStatus.CANCELLED}, ImpactStatus.APPLIED: {ImpactStatus.ACTIVE}, ImpactStatus.ACTIVE: {ImpactStatus.REVERSED, ImpactStatus.EXPIRED}}


@dataclass
class ImpactInstance:
    id: ImpactInstanceId
    definition: ImpactDefinition
    simulation_id: UUID
    scheduled_at: datetime
    correlation_id: UUID
    causation_id: UUID | None
    status: ImpactStatus = ImpactStatus.PENDING
    result: ImpactResult | None = None
    applied_changes: tuple[AppliedChange, ...] = ()
    audit_trail: tuple[object, ...] = ()

    def transition(self, status: ImpactStatus) -> None:
        if status not in _TRANSITIONS.get(self.status, set()):
            raise DomainRuleViolation(f"Invalid impact lifecycle transition: {self.status} -> {status}.")
        self.status = status


@dataclass
class ImpactEngine:
    simulation_id: UUID
    scenario_id: UUID
    instances: tuple[ImpactInstance, ...] = ()
    audit_trail: tuple[object, ...] = ()

    def create(self, simulation: Simulation, instance_id: UUID, definition: ImpactDefinition, correlation_id: UUID, causation_id: UUID | None = None) -> ImpactInstance:
        self._ensure(simulation)
        if definition.scenario_id != self.scenario_id or definition.source.session_id != self.simulation_id or any(i.id == instance_id for i in self.instances):
            raise DomainRuleViolation("Impact definition scope or instance identifier is invalid.")
        for change in definition.changes:
            if change.target.session_id != self.simulation_id or change.target.scenario_id != self.scenario_id:
                raise DomainRuleViolation("Impact target scope is invalid.")
            if change.target.target_type.value == "resource" and (change.target.target_id is None or not simulation.context.includes_resource(change.target.target_id)):
                raise DomainRuleViolation("Impact target resource is unavailable in this simulation scope.")
        item = ImpactInstance(ImpactInstanceId(instance_id), definition, self.simulation_id, simulation.current_time + timedelta(minutes=definition.delay_minutes), correlation_id, causation_id)
        item.transition(ImpactStatus.SCHEDULED if definition.delay_minutes else ImpactStatus.READY)
        self.instances = (*self.instances, item); self._record(item, ImpactCreated(self.simulation_id, self.scenario_id, item.id, definition.version, simulation.current_time, "created", correlation_id, causation_id))
        self._record(item, (ImpactScheduled if item.status is ImpactStatus.SCHEDULED else ImpactReady)(self.simulation_id, self.scenario_id, item.id, definition.version, simulation.current_time, item.status.value, correlation_id, causation_id))
        return item

    def refresh(self, simulation: Simulation) -> tuple[ImpactResult, ...]:
        self._ensure(simulation); results: list[ImpactResult] = []
        for item in sorted(self.instances, key=lambda x: (x.scheduled_at, -x.definition.priority, str(x.id))):
            if item.status is ImpactStatus.SCHEDULED and simulation.current_time >= item.scheduled_at:
                item.transition(ImpactStatus.READY); self._record(item, ImpactReady(self.simulation_id, self.scenario_id, item.id, item.definition.version, simulation.current_time, "ready", item.correlation_id, item.causation_id))
            if item.status is ImpactStatus.READY: results.append(self.apply(simulation, item.id))
            elif item.status is ImpactStatus.ACTIVE and item.definition.duration_minutes is not None and simulation.current_time >= item.scheduled_at + timedelta(minutes=item.definition.duration_minutes): item.transition(ImpactStatus.EXPIRED)
        return tuple(results)

    def apply(self, simulation: Simulation, instance_id: UUID) -> ImpactResult:
        self._ensure(simulation); item = self._item(instance_id)
        if item.status is not ImpactStatus.READY: raise DomainRuleViolation("Only READY impacts can be applied.")
        if not all(simulation.state.get(c.target.state_key) == c.expected_value for c in item.definition.conditions):
            item.transition(ImpactStatus.FAILED); self._record(item, ImpactFailed(self.simulation_id, self.scenario_id, item.id, item.definition.version, simulation.current_time, "conditions", item.correlation_id, item.causation_id)); raise DomainRuleViolation("Impact conditions are not satisfied.")
        before = simulation.state
        try: applied, skipped, values = self._calculate(before, item.definition.changes)
        except DomainRuleViolation as error:
            item.transition(ImpactStatus.FAILED); self._record(item, ImpactFailed(self.simulation_id, self.scenario_id, item.id, item.definition.version, simulation.current_time, str(error), item.correlation_id, item.causation_id)); raise
        after = before if not applied else before.with_values(values)
        if after is not before: simulation.replace_simulation_state(after)
        result = ImpactResult(item.id, self.simulation_id, self.scenario_id, item.definition.source, ImpactStatus.APPLIED, applied, skipped, tuple(x.reason for x in skipped), simulation.current_time, before.version, after.version, item.correlation_id, item.causation_id)
        item.applied_changes, item.result = applied, result; item.transition(ImpactStatus.ACTIVE if item.definition.temporary else ImpactStatus.APPLIED)
        if after is not before: self._record(item, ImpactApplied(self.simulation_id, self.scenario_id, item.id, item.definition.version, simulation.current_time, "applied", item.correlation_id, item.causation_id)); self._record(item, SimulationStateChanged(self.simulation_id, self.scenario_id, item.id, item.definition.version, simulation.current_time, "state changed", item.correlation_id, item.causation_id, before.version, after.version))
        return result

    def cancel(self, instance_id: ImpactInstanceId, occurred_at: datetime) -> None:
        item = self._item(instance_id); item.transition(ImpactStatus.CANCELLED); self._record(item, ImpactCancelled(self.simulation_id, self.scenario_id, item.id, item.definition.version, occurred_at, "cancelled", item.correlation_id, item.causation_id))

    def _calculate(self, state: SimulationState, changes: tuple[ImpactChange, ...]) -> tuple[tuple[AppliedChange, ...], tuple[SkippedChange, ...], tuple[StateValue, ...]]:
        values = {x.key: x.value for x in state.values}; applied: list[AppliedChange] = []; skipped: list[SkippedChange] = []
        for change in changes:
            try:
                old = values.get(change.target.state_key); new = self._operate(old, change)
                if isinstance(new, float) and not isfinite(new): raise DomainRuleViolation("Impact result is not finite.")
                if isinstance(new, (int, float)) and not isinstance(new, bool) and ((change.minimum is not None and new < change.minimum) or (change.maximum is not None and new > change.maximum)): raise DomainRuleViolation("Impact result violates bounds.")
                values[change.target.state_key] = new; applied.append(AppliedChange(change.target, old, new, change.operation))
            except DomainRuleViolation as error:
                if change.required: raise
                skipped.append(SkippedChange(change, str(error)))
        ordered = tuple(sorted((StateValue(k, v) for k, v in values.items()), key=lambda x: (x.key.target_type.value, str(x.key.target_id), x.key.attribute)))
        return tuple(applied), tuple(skipped), ordered

    @staticmethod
    def _operate(old: float | bool | None, change: ImpactChange) -> float | bool:
        if change.operation in {ImpactOperation.ACTIVATE, ImpactOperation.UNLOCK}: return True
        if change.operation in {ImpactOperation.DEACTIVATE, ImpactOperation.LOCK}: return False
        if isinstance(old, bool): raise DomainRuleViolation("Numeric operation cannot change boolean state.")
        number, value = (0.0 if old is None else float(old)), float(change.value)
        if change.operation is ImpactOperation.SET: return value
        if change.operation in {ImpactOperation.INCREASE, ImpactOperation.ADD, ImpactOperation.RESTORE, ImpactOperation.REPLENISH}: return number + value
        if change.operation in {ImpactOperation.DECREASE, ImpactOperation.SUBTRACT, ImpactOperation.DAMAGE, ImpactOperation.CONSUME}: return number - value
        if change.operation is ImpactOperation.MULTIPLY: return number * value
        if change.operation is ImpactOperation.DIVIDE:
            if value == 0: raise DomainRuleViolation("Division by zero is invalid.")
            return number / value
        if change.operation is ImpactOperation.MIN: return min(number, value)
        if change.operation is ImpactOperation.MAX: return max(number, value)
        raise DomainRuleViolation("Unsupported impact operation.")

    def _item(self, instance_id: UUID) -> ImpactInstance:
        item = next((x for x in self.instances if x.id == instance_id), None)
        if item is None: raise DomainRuleViolation("Impact instance is unavailable.")
        return item
    def _ensure(self, simulation: Simulation) -> None:
        if simulation.id != self.simulation_id: raise DomainRuleViolation("Impact engine belongs to another simulation.")
    def _record(self, item: ImpactInstance, event: object) -> None:
        if isinstance(event, ImpactCreated):
            event = replace(event, source=item.definition.source, target=item.definition.changes[0].target)
        item.audit_trail = (*item.audit_trail, event); self.audit_trail = (*self.audit_trail, event)

    def reverse(self, simulation: Simulation, instance_id: UUID) -> None:
        """Safe reversal remains a separately designed future stage."""
        self._ensure(simulation)
        self._item(instance_id)
        raise DomainRuleViolation("Safe impact reversal is not implemented.")
