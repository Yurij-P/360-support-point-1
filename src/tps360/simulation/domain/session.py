from enum import StrEnum
from hashlib import sha256
from secrets import compare_digest
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from tps360.core.exceptions import DomainRuleViolation, NotFoundError


class SessionStatus(StrEnum):
    LOBBY = "lobby"
    READY = "ready"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Participant(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    display_name: str = Field(min_length=1)
    role_id: UUID | None = None


class FacilitatedSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    community_id: UUID
    facilitator_name: str = Field(min_length=1)
    player_capacity: int = Field(ge=1)
    status: SessionStatus = SessionStatus.LOBBY
    participants: list[Participant] = Field(default_factory=list)
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

    def _participant(self, participant_id: UUID) -> Participant:
        for participant in self.participants:
            if participant.id == participant_id:
                return participant
        raise NotFoundError("Participant is not connected to this session")

    def _refresh_readiness(self) -> None:
        has_players = bool(self.participants)
        all_assigned = all(participant.role_id is not None for participant in self.participants)
        self.status = SessionStatus.READY if has_players and all_assigned else SessionStatus.LOBBY
