from dataclasses import dataclass
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation
from tps360.threats.domain import ThreatType

from .enums import ScenarioDifficulty, ScenarioType
from .scenario_metadata import ScenarioMetadata
from .scheduled_event import ScheduledEvent
from .timeline import TimelineEvent


@dataclass(frozen=True)
class ScenarioGoal:
    id: UUID
    description: str

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise DomainRuleViolation("Scenario goal description must not be empty.")


@dataclass(frozen=True)
class ScenarioPhase:
    name: str
    is_required: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainRuleViolation("Scenario phase name must not be empty.")


@dataclass(frozen=True)
class ScenarioDefinition:
    """Immutable, reusable definition for a crisis scenario."""

    id: UUID
    name: str
    description: str
    version: int
    scenario_type: ScenarioType
    difficulty: ScenarioDifficulty
    initial_conditions: tuple[str, ...]
    simulation_goals: tuple[ScenarioGoal, ...]
    completion_criteria: tuple[str, ...]
    initial_threat_ids: tuple[UUID, ...]
    planned_events: tuple[TimelineEvent, ...]
    allowed_team_roles: tuple[str, ...]
    metadata: ScenarioMetadata
    phases: tuple[ScenarioPhase, ...]
    required_territories: tuple[str, ...] = ()
    required_infrastructure: tuple[str, ...] = ()
    required_resource_ids: tuple[UUID, ...] = ()
    supported_threat_types: tuple[ThreatType, ...] = ()
    scheduled_events: tuple[ScheduledEvent, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.description.strip():
            raise DomainRuleViolation("Scenario name and description must not be empty.")
        if self.version < 1:
            raise DomainRuleViolation("Scenario version must be at least one.")
        self._validate_texts(self.initial_conditions, "Initial conditions")
        self._validate_texts(self.completion_criteria, "Completion criteria")
        self._validate_texts(self.allowed_team_roles, "Allowed team roles")
        self._validate_texts(self.required_territories, "Required territories")
        self._validate_texts(self.required_infrastructure, "Required infrastructure")
        self._validate_unique_ids(tuple(goal.id for goal in self.simulation_goals), "Scenario goal IDs")
        self._validate_unique_ids(self.initial_threat_ids, "Initial threat IDs")
        self._validate_unique_ids(self.required_resource_ids, "Required resource IDs")
        phase_names = tuple(phase.name for phase in self.phases)
        if len(set(phase_names)) != len(phase_names):
            raise DomainRuleViolation("Scenario phase names must be unique.")
        event_ids = tuple(event.id for event in self.planned_events)
        self._validate_unique_ids(event_ids, "Planned event IDs")
        if tuple(sorted(self.planned_events, key=lambda event: event.timestamp)) != self.planned_events:
            raise DomainRuleViolation("Planned events must be ordered by timestamp.")
        scheduled_event_ids = tuple(event.id for event in self.scheduled_events)
        self._validate_unique_ids(scheduled_event_ids, "Scheduled event IDs")
        if any(event.scenario_id != self.id for event in self.scheduled_events):
            raise DomainRuleViolation("Scheduled events must belong to the scenario definition.")
        if len(set(self.supported_threat_types)) != len(self.supported_threat_types):
            raise DomainRuleViolation("Supported threat types must not contain duplicates.")

    @staticmethod
    def _validate_texts(values: tuple[str, ...], label: str) -> None:
        if any(not value.strip() for value in values) or len(set(values)) != len(values):
            raise DomainRuleViolation(f"{label} must be non-empty and unique.")

    @staticmethod
    def _validate_unique_ids(values: tuple[UUID, ...], label: str) -> None:
        if len(set(values)) != len(values):
            raise DomainRuleViolation(f"{label} must not contain duplicates.")