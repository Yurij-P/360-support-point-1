from collections.abc import Callable
from secrets import token_urlsafe
from typing import Any, TypeVar
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from tps360.api.dependencies import sessions
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.simulation.domain.session import (
    FacilitatedSession,
    Participant,
    ParticipantDecision,
    RoleProfile,
    SessionInject,
    SessionJournalEntry,
    SessionStatus,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])
T = TypeVar("T")


class CreateSessionRequest(BaseModel):
    community_id: UUID
    facilitator_name: str = Field(min_length=1)
    player_capacity: int = Field(ge=1)
    role_profiles: list[RoleProfile] = Field(default_factory=list)


class JoinSessionRequest(BaseModel):
    display_name: str = Field(min_length=1)
    join_token: str | None = None
    participant_token: str | None = None


class AssignRoleRequest(BaseModel):
    role_id: UUID


class SendInjectRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class SubmitDecisionRequest(BaseModel):
    participant_id: UUID
    selected_action: str = Field(min_length=1)
    rationale: str | None = None


class SessionResponse(BaseModel):
    id: UUID
    community_id: UUID
    facilitator_name: str
    player_capacity: int
    status: SessionStatus
    participants: list[Participant]
    injects: list[SessionInject]
    decisions: list[ParticipantDecision]
    journal: list[SessionJournalEntry]
    role_profiles: list[RoleProfile]

    @classmethod
    def from_domain(cls, session: FacilitatedSession) -> "SessionResponse":
        return cls(**session.model_dump())


class CreateSessionResponse(SessionResponse):
    facilitator_token: str
    join_token: str


def item(session_id: UUID) -> FacilitatedSession:
    try:
        return sessions.get(session_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


def domain_action(action: Callable[[], T]) -> T:
    try:
        return action()
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except DomainRuleViolation as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("")
def create(request: CreateSessionRequest) -> CreateSessionResponse:
    facilitator_token = token_urlsafe(32)
    join_token = token_urlsafe(32)
    session = sessions.add(
        FacilitatedSession(
            **request.model_dump(),
            facilitator_token_digest=FacilitatedSession.digest_facilitator_token(
                facilitator_token
            ),
            join_token_digest=FacilitatedSession.digest_facilitator_token(join_token),
        )
    )
    return CreateSessionResponse(
        **session.model_dump(),
        facilitator_token=facilitator_token,
        join_token=join_token,
    )


class ParticipantViewResponse(BaseModel):
    participant_id: UUID
    display_name: str
    lifecycle: str
    reconnect_status: str
    role_assigned: bool
    role_id: UUID | None
    role_profile: RoleProfile | None
    session_status: SessionStatus

class ParticipantJoinResponse(ParticipantViewResponse):
    participant_token: str | None

@router.get("/{session_id}")
def get_session(session_id: UUID) -> SessionResponse:
    return SessionResponse.from_domain(item(session_id))


@router.post("/{session_id}/participants/join")
def join_participant(session_id: UUID, request: JoinSessionRequest) -> ParticipantJoinResponse:
    session = item(session_id)
    participant, participant_token = domain_action(
        lambda: session.join_participant(
            request.display_name, request.join_token, request.participant_token
        )
    )
    return ParticipantJoinResponse(
        participant_id=participant.id,
        display_name=participant.display_name,
        lifecycle=participant.lifecycle.value,
        reconnect_status=participant.reconnect_status,
        role_assigned=participant.role_id is not None,
        role_id=participant.role_id,
        role_profile=session.role_profile(participant.role_id),
        session_status=session.status,
        participant_token=participant_token,
    )

@router.post("/{session_id}/participants")
def join(session_id: UUID, request: JoinSessionRequest) -> Participant:
    session = item(session_id)
    return domain_action(lambda: session.join(request.display_name))

@router.get("/{session_id}/participant")
def get_participant(
    session_id: UUID,
    participant_token: str | None = Header(None, alias="X-Participant-Token"),
) -> ParticipantViewResponse:
    session = item(session_id)
    participant = authorize_participant(session, participant_token)
    return ParticipantViewResponse(
        participant_id=participant.id,
        display_name=participant.display_name,
        lifecycle=participant.lifecycle.value,
        reconnect_status=participant.reconnect_status,
        role_assigned=participant.role_id is not None,
        role_id=participant.role_id,
        role_profile=session.role_profile(participant.role_id),
        session_status=session.status,
    )


@router.put("/{session_id}/participants/{participant_id}/role")
def assign_role(
    session_id: UUID,
    participant_id: UUID,
    request: AssignRoleRequest,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> Participant:
    session = item(session_id)
    authorize_facilitator(session, facilitator_token)
    return domain_action(lambda: session.assign_role(participant_id, request.role_id))


@router.post("/{session_id}/start")
def start(
    session_id: UUID,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> SessionResponse:
    session = item(session_id)
    authorize_facilitator(session, facilitator_token)
    domain_action(session.start)
    return SessionResponse.from_domain(session)


@router.post("/{session_id}/injects")
def send_inject(
    session_id: UUID,
    request: SendInjectRequest,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> SessionInject:
    session = item(session_id)
    authorize_facilitator(session, facilitator_token)
    return domain_action(
        lambda: session.send_inject(
            request.title,
            request.description,
            request.payload,
        )
    )


@router.post("/{session_id}/injects/{inject_id}/decisions")
def submit_decision(
    session_id: UUID,
    inject_id: UUID,
    request: SubmitDecisionRequest,
) -> ParticipantDecision:
    session = item(session_id)
    return domain_action(
        lambda: session.submit_decision(
            inject_id,
            request.participant_id,
            request.selected_action,
            request.rationale,
        )
    )


@router.post("/{session_id}/complete")
def complete(
    session_id: UUID,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> SessionResponse:
    session = item(session_id)
    authorize_facilitator(session, facilitator_token)
    domain_action(session.complete)
    return SessionResponse.from_domain(session)


@router.get("/{session_id}/journal")
def get_journal(session_id: UUID) -> list[SessionJournalEntry]:
    return item(session_id).journal


def authorize_participant(session: FacilitatedSession, participant_token: str | None) -> Participant:
    if participant_token is None:
        raise HTTPException(401, "Participant token is required")
    try:
        return session.participant_for_token(participant_token)
    except DomainRuleViolation as exc:
        raise HTTPException(403, str(exc)) from exc

def authorize_facilitator(
    session: FacilitatedSession, facilitator_token: str | None
) -> None:
    if facilitator_token is None:
        raise HTTPException(401, "Facilitator token is required")
    if not session.accepts_facilitator_token(facilitator_token):
        raise HTTPException(403, "Facilitator token is invalid")
