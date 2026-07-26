from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, AsyncGenerator
from uuid import uuid4

from tps360.core.exceptions import DomainRuleViolation


class SessionEventType(StrEnum):
    SESSION_STATUS_CHANGED = "SESSION_STATUS_CHANGED"
    PARTICIPANT_JOINED = "PARTICIPANT_JOINED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROUND_STARTED = "ROUND_STARTED"
    ROUND_PROGRESSED = "ROUND_PROGRESSED"
    DIRECTIVE_CREATED = "DIRECTIVE_CREATED"
    DIRECTIVE_UPDATED = "DIRECTIVE_UPDATED"
    INJECT_SENT = "INJECT_SENT"


@dataclass(frozen=True)
class SessionEvent:
    id: str
    session_id: str
    event_type: SessionEventType
    payload: dict[str, Any] = field(default_factory=dict)
    target_role_id: str | None = None
    timestamp_round: int = 0
    timestamp_iso: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def is_visible_for_role(self, role_id: str | None) -> bool:
        if role_id is None:
            return True
        return self.target_role_id is None or self.target_role_id == role_id


class SessionEventBroadcaster:
    """In-memory event bus and broadcaster for real-time multiplayer simulation sessions."""

    def __init__(self) -> None:
        self._history: dict[str, list[SessionEvent]] = {}
        self._listeners: dict[str, set[asyncio.Queue[SessionEvent]]] = {}

    def publish(self, event: SessionEvent) -> None:
        if not event.session_id:
            raise DomainRuleViolation("Session event requires a session identifier.")

        if event.session_id not in self._history:
            self._history[event.session_id] = []
        self._history[event.session_id].append(event)

        queues = self._listeners.get(event.session_id, set())
        for q in list(queues):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def get_events(
        self,
        session_id: str,
        role_id: str | None = None,
        since_event_id: str | None = None,
    ) -> list[SessionEvent]:
        events = self._history.get(session_id, [])
        if since_event_id:
            idx = next((i for i, item in enumerate(events) if item.id == since_event_id), -1)
            if idx != -1:
                events = events[idx + 1 :]

        return [e for e in events if e.is_visible_for_role(role_id)]

    async def subscribe_stream(
        self,
        session_id: str,
        role_id: str | None = None,
    ) -> AsyncGenerator[SessionEvent, None]:
        q: asyncio.Queue[SessionEvent] = asyncio.Queue(maxsize=100)
        if session_id not in self._listeners:
            self._listeners[session_id] = set()
        self._listeners[session_id].add(q)

        try:
            while True:
                event = await q.get()
                if event.is_visible_for_role(role_id):
                    yield event
        finally:
            if session_id in self._listeners:
                self._listeners[session_id].discard(q)


# Singleton instance for API application
broadcaster = SessionEventBroadcaster()


def create_event(
    session_id: str,
    event_type: SessionEventType,
    payload: dict[str, Any],
    target_role_id: str | None = None,
    timestamp_round: int = 0,
) -> SessionEvent:
    return SessionEvent(
        id=str(uuid4()),
        session_id=session_id,
        event_type=event_type,
        payload=payload,
        target_role_id=target_role_id,
        timestamp_round=timestamp_round,
    )
