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


@dataclass(frozen=True)
class ScenarioLoaded:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
    occurred_at: datetime


@dataclass(frozen=True)
class ScenarioValidated:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
    occurred_at: datetime
    error_count: int
    warning_count: int


@dataclass(frozen=True)
class ScenarioActivated:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
    occurred_at: datetime


@dataclass(frozen=True)
class ScenarioSuspended:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
    occurred_at: datetime


@dataclass(frozen=True)
class ScenarioResumed:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
    occurred_at: datetime


@dataclass(frozen=True)
class ScenarioPhaseChanged:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
    occurred_at: datetime
    previous_phase: str | None
    current_phase: str


@dataclass(frozen=True)
class ScenarioCompleted:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
    occurred_at: datetime


@dataclass(frozen=True)
class ScenarioFailed:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
    occurred_at: datetime


@dataclass(frozen=True)
class ScenarioCancelled:
    simulation_id: UUID
    scenario_id: UUID
    scenario_version: int
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

ScenarioDomainEvent = (
    ScenarioLoaded
    | ScenarioValidated
    | ScenarioActivated
    | ScenarioSuspended
    | ScenarioResumed
    | ScenarioPhaseChanged
    | ScenarioCompleted
    | ScenarioFailed
    | ScenarioCancelled
)
@dataclass(frozen=True)
class EventScheduled:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class EventBlocked:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class EventReady:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class EventActivated:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class EventResolved:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class EventFailed:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class EventExpired:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class EventCancelled:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class RecurringEventOccurrenceCreated:
    simulation_id: UUID
    scenario_id: UUID
    event_id: UUID
    event_version: int
    occurrence_index: int
    occurred_at: datetime
    reason: str