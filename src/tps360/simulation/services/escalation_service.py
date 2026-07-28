"""Upward escalation / request contract for subordinate roles (ADR-0015 prereq #3).

Members and other subordinates may not issue directives, but they may raise an
escalation/request UP the command chain. Authorization uses
`command_hierarchy.can_escalate`. State is kept in memory, consistent with other
runtime services (event broadcaster, role dashboards).
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from tps360.core.exceptions import DomainRuleViolation


class EscalationStatus:
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


_VALID_STATUSES = frozenset({EscalationStatus.OPEN, EscalationStatus.ACKNOWLEDGED, EscalationStatus.RESOLVED})


@dataclass(frozen=True)
class EscalationRequest:
    escalation_id: str
    session_id: str
    requester_role_id: str
    target_role_id: str
    subject: str
    detail: str = ""
    status: str = EscalationStatus.OPEN
    created_at_round: int = 1


class EscalationService:
    """In-memory store of upward escalations raised by subordinate roles."""

    def __init__(self) -> None:
        self._by_session: dict[str, list[EscalationRequest]] = {}

    def raise_escalation(
        self,
        session_id: str,
        requester_role_id: str,
        target_role_id: str,
        subject: str,
        detail: str = "",
        current_round: int = 1,
    ) -> EscalationRequest:
        if not subject.strip():
            raise DomainRuleViolation("Escalation subject cannot be empty.")

        escalation = EscalationRequest(
            escalation_id=f"esc_{uuid4().hex[:8]}",
            session_id=session_id,
            requester_role_id=requester_role_id,
            target_role_id=target_role_id,
            subject=subject.strip(),
            detail=detail.strip(),
            created_at_round=current_round,
        )
        self._by_session.setdefault(session_id, []).append(escalation)
        return escalation

    def list_for_session(
        self, session_id: str, role_id: str | None = None
    ) -> list[EscalationRequest]:
        items = self._by_session.get(session_id, [])
        if role_id is None:
            return list(items)
        return [
            e for e in items if e.requester_role_id == role_id or e.target_role_id == role_id
        ]

    def set_status(self, session_id: str, escalation_id: str, new_status: str) -> EscalationRequest:
        if new_status not in _VALID_STATUSES:
            raise DomainRuleViolation(f"Unknown escalation status '{new_status}'.")
        items = self._by_session.get(session_id, [])
        for idx, e in enumerate(items):
            if e.escalation_id == escalation_id:
                updated = EscalationRequest(
                    escalation_id=e.escalation_id,
                    session_id=e.session_id,
                    requester_role_id=e.requester_role_id,
                    target_role_id=e.target_role_id,
                    subject=e.subject,
                    detail=e.detail,
                    status=new_status,
                    created_at_round=e.created_at_round,
                )
                items[idx] = updated
                return updated
        raise DomainRuleViolation(f"Escalation '{escalation_id}' not found in session.")
