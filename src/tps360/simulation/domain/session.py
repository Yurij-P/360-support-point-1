from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from secrets import compare_digest, token_urlsafe
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


class ParticipantLifecycle(StrEnum):
    ROLE_PENDING = "role_pending"
    ROLE_ASSIGNED = "role_assigned"


class Participant(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    display_name: str = Field(min_length=1)
    role_id: UUID | None = None
    lifecycle: ParticipantLifecycle = ParticipantLifecycle.ROLE_PENDING
    reconnect_status: str = "new"
    participant_token_digest: str | None = Field(default=None, exclude=True, repr=False)


class RoleProfile(BaseModel):
    role_id: UUID
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    briefing: str = Field(min_length=1)
    allowed_actions: list[str] = Field(default_factory=list)
    visibility_rules: list[str] = Field(default_factory=list)


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
    join_token_digest: str = Field(default="", exclude=True, repr=False)
    role_profiles: list[RoleProfile] = Field(default_factory=list)

    @staticmethod
    def digest_facilitator_token(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def digest_participant_token(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()

    def accepts_facilitator_token(self, token: str) -> bool:
        return compare_digest(
            self.facilitator_token_digest,
            self.digest_facilitator_token(token),
        )

    def accepts_join_token(self, token: str) -> bool:
        return compare_digest(self.join_token_digest, self.digest_facilitator_token(token))

    def join_participant(
        self,
        display_name: str,
        join_token: str | None = None,
        participant_token: str | None = None,
    ) -> tuple[Participant, str | None]:
        if participant_token is not None:
            participant = self.participant_for_token(participant_token)
            participant.reconnect_status = "restored"
            return participant, None
        if join_token is None or not self.accepts_join_token(join_token):
            raise DomainRuleViolation("Join token is invalid")
        if self.status not in {SessionStatus.LOBBY, SessionStatus.READY}:
            raise DomainRuleViolation("Players can join only before the session starts")
        if len(self.participants) >= self.player_capacity:
            raise DomainRuleViolation("Session player capacity has been reached")
        token = token_urlsafe(32)
        participant = Participant(
            display_name=display_name,
            participant_token_digest=self.digest_participant_token(token),
        )
        self.participants.append(participant)
        self._refresh_readiness()
        return participant, token

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
        if not any(profile.role_id == role_id for profile in self.role_profiles):
            raise DomainRuleViolation("Role is not available in this session")
        participant.role_id = role_id
        participant.lifecycle = ParticipantLifecycle.ROLE_ASSIGNED
        self._refresh_readiness()
        return participant

    def participant_for_token(self, token: str) -> Participant:
        token_digest = self.digest_participant_token(token)
        for participant in self.participants:
            if participant.participant_token_digest and compare_digest(
                participant.participant_token_digest, token_digest
            ):
                return participant
        raise DomainRuleViolation("Participant token is invalid")

    def role_profile(self, role_id: UUID | None) -> RoleProfile | None:
        if role_id is None:
            return None
        return next(
            (profile for profile in self.role_profiles if profile.role_id == role_id),
            None,
        )

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
