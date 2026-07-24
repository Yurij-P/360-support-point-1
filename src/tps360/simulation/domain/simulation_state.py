from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation

from .enums import ImpactTargetType


@dataclass(frozen=True)
class StateKey:
    target_type: ImpactTargetType
    target_id: UUID | None
    field: str

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise DomainRuleViolation("Simulation state field must not be empty.")


@dataclass(frozen=True)
class StateValue:
    key: StateKey
    value: float | bool

    def __post_init__(self) -> None:
        if isinstance(self.value, float) and not isfinite(self.value):
            raise DomainRuleViolation("Simulation state cannot contain non-finite values.")


@dataclass(frozen=True)
class SimulationState:
    """Immutable, versioned state owned by one simulation session."""

    simulation_id: UUID
    version: int = 0
    values: tuple[StateValue, ...] = ()

    def __post_init__(self) -> None:
        if self.version < 0:
            raise DomainRuleViolation("Simulation state version cannot be negative.")
        if len({value.key for value in self.values}) != len(self.values):
            raise DomainRuleViolation("Simulation state keys must be unique.")

    def get(self, key: StateKey) -> float | bool | None:
        for value in self.values:
            if value.key == key:
                return value.value
        return None

    def with_values(self, values: tuple[StateValue, ...]) -> SimulationState:
        return SimulationState(self.simulation_id, self.version + 1, values)