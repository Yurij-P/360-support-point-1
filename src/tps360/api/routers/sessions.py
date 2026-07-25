from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tps360.api.dependencies import sessions
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.simulation.domain.session import FacilitatedSession, Participant

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


def item(session_id: UUID) -> FacilitatedSession:
    try:
        return sessions.get(session_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


def domain_action(action: Callable[[], T]) -> T:
    try:
        return action()
    except DomainRuleViolation as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("")
def create(request: CreateSessionRequest) -> FacilitatedSession:
    return sessions.add(FacilitatedSession(**request.model_dump()))


@router.get("/{session_id}")
def get_session(session_id: UUID) -> FacilitatedSession:
    return item(session_id)


@router.post("/{session_id}/participants")
def join(session_id: UUID, request: JoinSessionRequest) -> Participant:
    session = item(session_id)
    return domain_action(lambda: session.join(request.display_name))


@router.put("/{session_id}/participants/{participant_id}/role")
def assign_role(
    session_id: UUID, participant_id: UUID, request: AssignRoleRequest
) -> Participant:
    session = item(session_id)
    return domain_action(lambda: session.assign_role(participant_id, request.role_id))


@router.post("/{session_id}/start")
def start(session_id: UUID) -> FacilitatedSession:
    session = item(session_id)
    domain_action(session.start)
    return session
