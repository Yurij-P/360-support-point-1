from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from .enums import ImpactConflictPolicy
from .impact_contracts import ImpactInstanceId, ImpactSourceReference, TypedImpactTarget
from .simulation_state import StateKey


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

@dataclass(frozen=True)
class DecisionRequestCreated:
    simulation_id: UUID
    scenario_id: UUID
    request_id: UUID
    request_version: int
    occurred_at: datetime
    reason: str


@dataclass(frozen=True)
class DecisionRequestOpened(DecisionRequestCreated):
    pass


@dataclass(frozen=True)
class DecisionSubmitted(DecisionRequestCreated):
    submission_id: UUID


@dataclass(frozen=True)
class DecisionSubmissionValidated(DecisionSubmitted):
    pass


@dataclass(frozen=True)
class DecisionSubmissionWithdrawn(DecisionSubmitted):
    pass


@dataclass(frozen=True)
class DecisionReviewStarted(DecisionRequestCreated):
    pass


@dataclass(frozen=True)
class DecisionApprovalRecorded(DecisionRequestCreated):
    role_id: UUID


@dataclass(frozen=True)
class DecisionRejectionRecorded(DecisionApprovalRecorded):
    pass


@dataclass(frozen=True)
class DecisionApproved(DecisionRequestCreated):
    pass


@dataclass(frozen=True)
class DecisionRejected(DecisionRequestCreated):
    pass


@dataclass(frozen=True)
class DecisionExecuted(DecisionRequestCreated):
    pass


@dataclass(frozen=True)
class DecisionExpired(DecisionRequestCreated):
    pass


@dataclass(frozen=True)
class DecisionCancelled(DecisionRequestCreated):
    pass


@dataclass(frozen=True)
class DecisionOutcomeCreated(DecisionRequestCreated):
    correlation_id: UUID
    causation_id: UUID | None

@dataclass(frozen=True)
class ImpactCreated:
    simulation_id: UUID
    scenario_id: UUID
    impact_id: UUID
    impact_version: int
    occurred_at: datetime
    reason: str
    correlation_id: UUID
    causation_id: UUID | None
    source: ImpactSourceReference | None = field(default=None, kw_only=True)
    target: TypedImpactTarget | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class ImpactScheduled(ImpactCreated):
    pass


@dataclass(frozen=True)
class ImpactReady(ImpactCreated):
    pass


@dataclass(frozen=True)
class ImpactApplied(ImpactCreated):
    pass


@dataclass(frozen=True)
class ImpactActivated(ImpactCreated):
    pass


@dataclass(frozen=True)
class ImpactReversed(ImpactCreated):
    pass


@dataclass(frozen=True)
class ImpactExpired(ImpactCreated):
    pass


@dataclass(frozen=True)
class ImpactCancelled(ImpactCreated):
    pass


@dataclass(frozen=True)
class ImpactFailed(ImpactCreated):
    pass


@dataclass(frozen=True)
class SimulationStateChanged(ImpactCreated):
    state_version_before: int = 0
    state_version_after: int = 0


@dataclass(frozen=True)
class ImpactConflictDetected(ImpactCreated):
    conflicting_impact_ids: tuple[ImpactInstanceId, ...] = ()
    state_keys: tuple[StateKey, ...] = ()
    policy: ImpactConflictPolicy = ImpactConflictPolicy.REJECT
# Impact lifecycle events are intentionally separate from the historical simulation-only union.
ImpactDomainEvent = (
    ImpactCreated
    | ImpactScheduled
    | ImpactReady
    | ImpactApplied
    | ImpactActivated
    | ImpactReversed
    | ImpactExpired
    | ImpactCancelled
    | ImpactFailed
    | SimulationStateChanged
    | ImpactConflictDetected
)
