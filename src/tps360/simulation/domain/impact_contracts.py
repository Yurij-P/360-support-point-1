from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, NewType
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation

from .enums import ImpactSourceType, ImpactTargetType

if TYPE_CHECKING:
    from .simulation_state import StateKey

ImpactDefinitionId = NewType("ImpactDefinitionId", UUID)
ImpactInstanceId = NewType("ImpactInstanceId", UUID)
EventId = NewType("EventId", UUID)
EventOccurrenceId = NewType("EventOccurrenceId", UUID)
DecisionOutcomeId = NewType("DecisionOutcomeId", UUID)


class ImpactAttribute(StrEnum):
    QUANTITY = "quantity"
    STATUS = "status"
    CAPACITY = "capacity"
    LEVEL = "level"
    POPULATION = "population"
    DAMAGE = "damage"


_ALLOWED: dict[ImpactTargetType, frozenset[ImpactAttribute]] = {
    ImpactTargetType.SIMULATION: frozenset({ImpactAttribute.STATUS, ImpactAttribute.LEVEL}),
    ImpactTargetType.TERRITORY: frozenset({ImpactAttribute.LEVEL, ImpactAttribute.DAMAGE}),
    ImpactTargetType.SETTLEMENT: frozenset({ImpactAttribute.POPULATION, ImpactAttribute.DAMAGE}),
    ImpactTargetType.POPULATION_GROUP: frozenset({ImpactAttribute.POPULATION, ImpactAttribute.LEVEL}),
    ImpactTargetType.INFRASTRUCTURE: frozenset({ImpactAttribute.STATUS, ImpactAttribute.CAPACITY, ImpactAttribute.DAMAGE}),
    ImpactTargetType.RESOURCE: frozenset({ImpactAttribute.QUANTITY, ImpactAttribute.STATUS}),
    ImpactTargetType.THREAT: frozenset({ImpactAttribute.LEVEL, ImpactAttribute.STATUS}),
    ImpactTargetType.SERVICE: frozenset({ImpactAttribute.CAPACITY, ImpactAttribute.STATUS}),
    ImpactTargetType.CAPABILITY: frozenset({ImpactAttribute.LEVEL, ImpactAttribute.STATUS}),
}


@dataclass(frozen=True)
class ImpactSourceReference:
    source_type: ImpactSourceType
    session_id: UUID
    scenario_id: UUID
    event_id: EventId | None = None
    occurrence_id: EventOccurrenceId | None = None
    decision_outcome_id: DecisionOutcomeId | None = None
    source_impact_id: ImpactInstanceId | None = None

    def __post_init__(self) -> None:
        event = self.event_id is not None and self.occurrence_id is not None
        if (self.event_id is None) != (self.occurrence_id is None):
            raise DomainRuleViolation("Event source requires both event and occurrence identifiers.")
        decision, reversal = self.decision_outcome_id is not None, self.source_impact_id is not None
        valid = {ImpactSourceType.EVENT: event and not decision and not reversal, ImpactSourceType.DECISION: decision and not event and not reversal, ImpactSourceType.COMBINED: event and decision and not reversal, ImpactSourceType.SYSTEM: not event and not decision and not reversal, ImpactSourceType.REVERSAL: reversal and not event and not decision}
        if not valid[self.source_type]:
            raise DomainRuleViolation("Invalid ImpactSourceReference field combination.")


@dataclass(frozen=True)
class TypedImpactTarget:
    target_type: ImpactTargetType
    target_id: UUID | None
    attribute: ImpactAttribute
    session_id: UUID
    scenario_id: UUID

    def __post_init__(self) -> None:
        if self.target_type is ImpactTargetType.SIMULATION:
            if self.target_id is not None: raise DomainRuleViolation("Simulation target cannot have an identifier.")
        elif self.target_id is None: raise DomainRuleViolation("Target identifier is required.")
        if self.attribute not in _ALLOWED[self.target_type]: raise DomainRuleViolation("Target attribute is not supported.")

    @property
    def state_key(self) -> "StateKey":
        from .simulation_state import StateKey
        return StateKey(self.target_type, self.target_id, self.attribute.value)
