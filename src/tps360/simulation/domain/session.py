from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from tps360.core.exceptions import DomainRuleViolation


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

    def join(self, display_name: str) -> Participant:
        if self.status is not SessionStatus.LOBBY:
            raise DomainRuleViolation("Players can join only while the session is in the lobby")
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
        if not self.participants:
            raise DomainRuleViolation("A session requires at least one connected player")
        if any(participant.role_id is None for participant in self.participants):
            raise DomainRuleViolation("Every connected player must have an assigned role")
        self.status = SessionStatus.ACTIVE

    def _participant(self, participant_id: UUID) -> Participant:
        for participant in self.participants:
            if participant.id == participant_id:
                return participant
        raise DomainRuleViolation("Participant is not connected to this session")

    def _refresh_readiness(self) -> None:
        has_players = bool(self.participants)
        all_assigned = all(participant.role_id is not None for participant in self.participants)
        self.status = SessionStatus.READY if has_players and all_assigned else SessionStatus.LOBBY
