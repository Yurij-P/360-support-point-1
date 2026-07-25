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
    attribute: str

    def __post_init__(self) -> None:
        if not self.attribute:
            raise DomainRuleViolation("Simulation state requires a typed target attribute.")
        if self.target_type is ImpactTargetType.SIMULATION and self.target_id is not None:
            raise DomainRuleViolation("Simulation state target cannot have an identifier.")
        if self.target_type is not ImpactTargetType.SIMULATION and self.target_id is None:
            raise DomainRuleViolation("Simulation state target identifier is required.")


@dataclass(frozen=True)
class StateValue:
    key: StateKey
    value: float | bool

    def __post_init__(self) -> None:
        if isinstance(self.value, float) and not isfinite(self.value):
            raise DomainRuleViolation("Simulation state cannot contain non-finite values.")


@dataclass(frozen=True)
class SimulationState:
    simulation_id: UUID
    version: int = 0
    values: tuple[StateValue, ...] = ()

    def __post_init__(self) -> None:
        if self.version < 0 or len({value.key for value in self.values}) != len(self.values):
            raise DomainRuleViolation("Simulation state version or keys are invalid.")

    def get(self, key: StateKey) -> float | bool | None:
        return next((item.value for item in self.values if item.key == key), None)

    def with_values(self, values: tuple[StateValue, ...]) -> SimulationState:
        return SimulationState(self.simulation_id, self.version + 1, values)
