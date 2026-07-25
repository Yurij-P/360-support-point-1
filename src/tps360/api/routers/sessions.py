from collections.abc import Callable
from secrets import token_urlsafe
from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from tps360.api.dependencies import sessions
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.simulation.domain.session import (
    FacilitatedSession,
    Participant,
    SessionStatus,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])
T = TypeVar("T")


class CreateSessionRequest(BaseModel):
    community_id: UUID
    facilitator_name: str = Field(min_length=1)
    player_capacity: int = Field(ge=1)


class JoinSessionRequest(BaseModel):
    display_name: str = Field(min_length=1)


class AssignRoleRequest(BaseModel):
    role_id: UUID


class SessionResponse(BaseModel):
    id: UUID
    community_id: UUID
    facilitator_name: str
    player_capacity: int
    status: SessionStatus
    participants: list[Participant]

    @classmethod
    def from_domain(cls, session: FacilitatedSession) -> "SessionResponse":
        return cls(**session.model_dump())


class CreateSessionResponse(SessionResponse):
    facilitator_token: str


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
    session = sessions.add(
        FacilitatedSession(
            **request.model_dump(),
            facilitator_token_digest=FacilitatedSession.digest_facilitator_token(
                facilitator_token
            ),
        )
    )
    return CreateSessionResponse(
        **session.model_dump(),
        facilitator_token=facilitator_token,
    )


@router.get("/{session_id}")
def get_session(session_id: UUID) -> SessionResponse:
    return SessionResponse.from_domain(item(session_id))


@router.post("/{session_id}/participants")
def join(session_id: UUID, request: JoinSessionRequest) -> Participant:
    session = item(session_id)
    return domain_action(lambda: session.join(request.display_name))


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


def authorize_facilitator(
    session: FacilitatedSession, facilitator_token: str | None
) -> None:
    if facilitator_token is None:
        raise HTTPException(401, "Facilitator token is required")
    if not session.accepts_facilitator_token(facilitator_token):
        raise HTTPException(403, "Facilitator token is invalid")
