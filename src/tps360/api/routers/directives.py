from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.task_directive import (
    DirectivePriority,
    DirectiveStatus,
    TaskDirective,
)

router = APIRouter(prefix="/directives", tags=["directives"])

_DIRECTIVES_STORE: dict[str, TaskDirective] = {}


class CreateDirectiveRequest(BaseModel):
    session_id: str = Field(min_length=1)
    issuer_role_id: str = Field(min_length=1)
    assignee_role_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(default="")
    target_round: int = Field(ge=1)
    task_execution_id: str | None = None
    priority: DirectivePriority = DirectivePriority.NORMAL
    created_at_round: int = Field(default=0, ge=0)


class DirectiveTransitionRequest(BaseModel):
    new_status: DirectiveStatus
    round_number: int = Field(ge=0)
    completion_report: str | None = None


class DirectiveResponse(BaseModel):
    id: str
    session_id: str
    issuer_role_id: str
    assignee_role_id: str
    title: str
    description: str
    target_round: int
    task_execution_id: str | None
    status: DirectiveStatus
    priority: DirectivePriority
    completion_report: str | None
    created_at_round: int
    completed_at_round: int | None
    is_terminal: bool


def _to_response(directive: TaskDirective) -> DirectiveResponse:
    return DirectiveResponse(
        id=directive.id,
        session_id=directive.session_id,
        issuer_role_id=directive.issuer_role_id,
        assignee_role_id=directive.assignee_role_id,
        title=directive.title,
        description=directive.description,
        target_round=directive.target_round,
        task_execution_id=directive.task_execution_id,
        status=directive.status,
        priority=directive.priority,
        completion_report=directive.completion_report,
        created_at_round=directive.created_at_round,
        completed_at_round=directive.completed_at_round,
        is_terminal=directive.is_terminal,
    )


@router.post("", response_model=DirectiveResponse)
def create_directive(req: CreateDirectiveRequest) -> DirectiveResponse:
    directive_id = str(uuid4())
    try:
        directive = TaskDirective(
            id=directive_id,
            session_id=req.session_id,
            issuer_role_id=req.issuer_role_id,
            assignee_role_id=req.assignee_role_id,
            title=req.title,
            description=req.description,
            target_round=req.target_round,
            task_execution_id=req.task_execution_id,
            priority=req.priority,
            created_at_round=req.created_at_round,
        )
    except DomainRuleViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _DIRECTIVES_STORE[directive_id] = directive
    return _to_response(directive)


@router.get("/{directive_id}", response_model=DirectiveResponse)
def get_directive(directive_id: str) -> DirectiveResponse:
    directive = _DIRECTIVES_STORE.get(directive_id)
    if directive is None:
        raise HTTPException(status_code=404, detail="Directive not found.")
    return _to_response(directive)


@router.post("/{directive_id}/transition", response_model=DirectiveResponse)
def transition_directive(
    directive_id: str, req: DirectiveTransitionRequest
) -> DirectiveResponse:
    directive = _DIRECTIVES_STORE.get(directive_id)
    if directive is None:
        raise HTTPException(status_code=404, detail="Directive not found.")

    try:
        updated = directive.transition(
            new_status=req.new_status,
            round_number=req.round_number,
            completion_report=req.completion_report,
        )
    except DomainRuleViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _DIRECTIVES_STORE[directive_id] = updated
    return _to_response(updated)


@router.get("/session/{session_id}", response_model=list[DirectiveResponse])
def list_session_directives(
    session_id: str, role_id: str | None = None
) -> list[DirectiveResponse]:
    matched = [
        directive
        for directive in _DIRECTIVES_STORE.values()
        if directive.session_id == session_id
        and (
            role_id is None
            or directive.assignee_role_id == role_id
            or directive.issuer_role_id == role_id
        )
    ]
    return [_to_response(item) for item in matched]
