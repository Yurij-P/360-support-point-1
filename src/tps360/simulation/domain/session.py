from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from secrets import compare_digest
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from tps360.core.exceptions import DomainRuleViolation, NotFoundError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SessionStatus(StrEnum):
    LOBBY = "lobby"
    READY = "ready"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionJournalEntryType(StrEnum):
    SESSION_STARTED = "session_started"
    INJECT_SENT = "inject_sent"
    DECISION_SUBMITTED = "decision_submitted"
    SESSION_COMPLETED = "session_completed"


class Participant(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    display_name: str = Field(min_length=1)
    role_id: UUID | None = None


class SessionInject(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    sent_at: datetime = Field(default_factory=utcnow)


class ParticipantDecision(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    inject_id: UUID
    participant_id: UUID
    role_id: UUID
    selected_action: str = Field(min_length=1)
    rationale: str | None = None
    submitted_at: datetime = Field(default_factory=utcnow)


class SessionJournalEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: SessionJournalEntryType
    message: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=utcnow)
    inject_id: UUID | None = None
    participant_id: UUID | None = None
    role_id: UUID | None = None
    decision_id: UUID | None = None


class FacilitatedSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    community_id: UUID
    facilitator_name: str = Field(min_length=1)
    player_capacity: int = Field(ge=1)
    status: SessionStatus = SessionStatus.LOBBY
    participants: list[Participant] = Field(default_factory=list)
    injects: list[SessionInject] = Field(default_factory=list)
    decisions: list[ParticipantDecision] = Field(default_factory=list)
    journal: list[SessionJournalEntry] = Field(default_factory=list)
    facilitator_token_digest: str = Field(exclude=True, repr=False)

    @staticmethod
    def digest_facilitator_token(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()

    def accepts_facilitator_token(self, token: str) -> bool:
        return compare_digest(
            self.facilitator_token_digest,
            self.digest_facilitator_token(token),
        )

    def join(self, display_name: str) -> Participant:
        if self.status not in {SessionStatus.LOBBY, SessionStatus.READY}:
            raise DomainRuleViolation("Players can join only before the session starts")
        if len(self.participants) >= self.player_capacity:
            raise DomainRuleViolation("Session player capacity has been reached")
        participant = Participant(display_name=display_name)
        self.participants.append(participant)
        self._refresh_readiness()
        return participant

    def assign_role(self, participant_id: UUID, role_id: UUID) -> Participant:
        if self.status not in {SessionStatus.LOBBY, SessionStatus.READY}:
            raise DomainRuleViolation("Roles can be assigned only before the session starts")
        participant = self._participant(participant_id)
        participant.role_id = role_id
        self._refresh_readiness()
        return participant

    def start(self) -> None:
        if self.status is not SessionStatus.READY:
            raise DomainRuleViolation("Only a ready session can be started")
        self.status = SessionStatus.ACTIVE
        self._record(
            SessionJournalEntryType.SESSION_STARTED,
            "Session started by facilitator",
        )

    def send_inject(
        self,
        title: str,
        description: str,
        payload: dict[str, Any] | None = None,
    ) -> SessionInject:
        self._require_active("Injects can be sent only during an active session")
        inject = SessionInject(title=title, description=description, payload=payload or {})
        self.injects.append(inject)
        self._record(
            SessionJournalEntryType.INJECT_SENT,
            f"Inject sent: {inject.title}",
            inject_id=inject.id,
        )
        return inject

    def submit_decision(
        self,
        inject_id: UUID,
        participant_id: UUID,
        selected_action: str,
        rationale: str | None = None,
    ) -> ParticipantDecision:
        self._require_active("Decisions can be submitted only during an active session")
        self._inject(inject_id)
        participant = self._participant(participant_id)
        if participant.role_id is None:
            raise DomainRuleViolation("Participant must have an assigned role to submit decisions")
        if any(
            decision.inject_id == inject_id and decision.participant_id == participant_id
            for decision in self.decisions
        ):
            raise DomainRuleViolation("Participant already submitted a decision for this inject")

        decision = ParticipantDecision(
            inject_id=inject_id,
            participant_id=participant_id,
            role_id=participant.role_id,
            selected_action=selected_action,
            rationale=rationale,
        )
        self.decisions.append(decision)
        self._record(
            SessionJournalEntryType.DECISION_SUBMITTED,
            f"Decision submitted by participant {participant.id}",
            inject_id=inject_id,
            participant_id=participant.id,
            role_id=participant.role_id,
            decision_id=decision.id,
        )
        return decision

    def complete(self) -> None:
        self._require_active("Only an active session can be completed")
        self.status = SessionStatus.COMPLETED
        self._record(
            SessionJournalEntryType.SESSION_COMPLETED,
            "Session completed by facilitator",
        )

    def _participant(self, participant_id: UUID) -> Participant:
        for participant in self.participants:
            if participant.id == participant_id:
                return participant
        raise NotFoundError("Participant is not connected to this session")

    def _inject(self, inject_id: UUID) -> SessionInject:
        for inject in self.injects:
            if inject.id == inject_id:
                return inject
        raise NotFoundError("Inject is not part of this session")

    def _refresh_readiness(self) -> None:
        has_players = bool(self.participants)
        all_assigned = all(participant.role_id is not None for participant in self.participants)
        self.status = SessionStatus.READY if has_players and all_assigned else SessionStatus.LOBBY

    def _require_active(self, message: str) -> None:
        if self.status is not SessionStatus.ACTIVE:
            raise DomainRuleViolation(message)

    def _record(
        self,
        entry_type: SessionJournalEntryType,
        message: str,
        inject_id: UUID | None = None,
        participant_id: UUID | None = None,
        role_id: UUID | None = None,
        decision_id: UUID | None = None,
    ) -> None:
        self.journal.append(
            SessionJournalEntry(
                type=entry_type,
                message=message,
                inject_id=inject_id,
                participant_id=participant_id,
                role_id=role_id,
                decision_id=decision_id,
            )
        )
