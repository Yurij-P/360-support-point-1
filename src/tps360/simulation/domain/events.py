from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SimulationPrepared:
    simulation_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SimulationStarted:
    simulation_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SimulationPaused:
    simulation_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SimulationResumed:
    simulation_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SimulationTimeAdvanced:
    simulation_id: UUID
    occurred_at: datetime
    requested_minutes: int
    elapsed_simulation_minutes: float


@dataclass(frozen=True)
class SimulationCompleted:
    simulation_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SimulationCancelled:
    simulation_id: UUID
    occurred_at: datetime


SimulationDomainEvent = (
    SimulationPrepared
    | SimulationStarted
    | SimulationPaused
    | SimulationResumed
    | SimulationTimeAdvanced
    | SimulationCompleted
    | SimulationCancelled
)