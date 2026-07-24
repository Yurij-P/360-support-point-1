from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation


@dataclass(frozen=True)
class TimelineEvent:
    """A simulation event scheduled at a concrete point in time."""

    id: UUID
    timestamp: datetime
    name: str
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainRuleViolation("Timeline event name must not be empty.")
        if not self.description.strip():
            raise DomainRuleViolation("Timeline event description must not be empty.")


@dataclass(frozen=True)
class Timeline:
    """An ordered collection of timestamped simulation events."""

    events: tuple[TimelineEvent, ...] = ()

    def __post_init__(self) -> None:
        event_ids = tuple(event.id for event in self.events)
        if len(set(event_ids)) != len(event_ids):
            raise DomainRuleViolation("Timeline event IDs must be unique.")
        if tuple(sorted(self.events, key=lambda event: event.timestamp)) != self.events:
            raise DomainRuleViolation("Timeline events must be ordered by timestamp.")

    def add_event(self, event: TimelineEvent) -> Timeline:
        if any(existing.id == event.id for existing in self.events):
            raise DomainRuleViolation("Timeline event IDs must be unique.")
        return Timeline(tuple(sorted((*self.events, event), key=lambda item: item.timestamp)))

    def events_until(self, current_time: datetime) -> tuple[TimelineEvent, ...]:
        return tuple(event for event in self.events if event.timestamp <= current_time)