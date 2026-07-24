from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation

from .enums import (
    ActivationConditionType,
    DependencyRule,
    EventPriority,
    EventRuntimeStatus,
    ScheduledEventType,
)
from .scenario_metadata import ScenarioMetadata


@dataclass(frozen=True)
class EventDependency:
    event_id: UUID
    required: bool = True


@dataclass(frozen=True)
class ActivationCondition:
    condition_type: ActivationConditionType
    key: str
    expected_value: str | int | float | bool | None = None
    event_id: UUID | None = None
    expected_event_status: EventRuntimeStatus | None = None

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise DomainRuleViolation("Activation condition key must not be empty.")
        if self.condition_type is ActivationConditionType.EVENT_STATUS_IS and (
            self.event_id is None or self.expected_event_status is None
        ):
            raise DomainRuleViolation("Event status conditions require an event ID and expected status.")


@dataclass(frozen=True)
class EventParameter:
    key: str
    value: str | int | float | bool

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise DomainRuleViolation("Event parameter key must not be empty.")


@dataclass(frozen=True)
class ScheduledEvent:
    """Immutable event definition loaded by an EventScheduler."""

    id: UUID
    scenario_id: UUID
    name: str
    description: str
    event_type: ScheduledEventType
    priority: EventPriority
    scenario_phase: str | None
    scheduled_time: datetime | None
    activation_conditions: tuple[ActivationCondition, ...]
    dependencies: tuple[EventDependency, ...]
    dependency_rule: DependencyRule
    target_territories: tuple[str, ...]
    target_infrastructure: tuple[str, ...]
    target_resource_ids: tuple[UUID, ...]
    target_population_groups: tuple[str, ...]
    parameters: tuple[EventParameter, ...]
    mandatory: bool
    repeat_count: int
    recurrence_interval_minutes: int | None
    metadata: ScenarioMetadata
    version: int
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.description.strip():
            raise DomainRuleViolation("Scheduled event name and description must not be empty.")
        if self.version < 1 or self.repeat_count < 0:
            raise DomainRuleViolation("Event version and repeat count must be non-negative and valid.")
        if self.event_type in {ScheduledEventType.TIME_BASED, ScheduledEventType.RECURRING} and (
            self.scheduled_time is None
        ):
            raise DomainRuleViolation("Time-based and recurring events require a scheduled time.")
        if self.event_type is ScheduledEventType.RECURRING and (
            self.recurrence_interval_minutes is None or self.recurrence_interval_minutes <= 0
        ):
            raise DomainRuleViolation("Recurring events require a positive recurrence interval.")
        if self.recurrence_interval_minutes is not None and self.recurrence_interval_minutes <= 0:
            raise DomainRuleViolation("Recurrence interval must be positive.")
        if self.expires_at is not None and self.scheduled_time is not None and self.expires_at < self.scheduled_time:
            raise DomainRuleViolation("Event expiration cannot precede its scheduled time.")
        self._validate_texts(self.target_territories, "Target territories")
        self._validate_texts(self.target_infrastructure, "Target infrastructure")
        self._validate_texts(self.target_population_groups, "Target population groups")
        if len(set(self.target_resource_ids)) != len(self.target_resource_ids):
            raise DomainRuleViolation("Target resource IDs must not contain duplicates.")
        if len({dependency.event_id for dependency in self.dependencies}) != len(self.dependencies):
            raise DomainRuleViolation("Event dependencies must not contain duplicates.")
        if len({parameter.key for parameter in self.parameters}) != len(self.parameters):
            raise DomainRuleViolation("Event parameter keys must be unique.")

    @staticmethod
    def _validate_texts(values: tuple[str, ...], label: str) -> None:
        if any(not value.strip() for value in values) or len(set(values)) != len(values):
            raise DomainRuleViolation(f"{label} must be non-empty and unique.")