from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.services.command_hierarchy import can_escalate
from tps360.simulation.services.escalation_service import (
    EscalationRequest,
    EscalationService,
)

router = APIRouter(prefix="/sessions", tags=["escalations"])
_service = EscalationService()


class RaiseEscalationRequest(BaseModel):
    requester_role_id: str = Field(min_length=1)
    target_role_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    detail: str = ""
    current_round: int = Field(default=1, ge=1)


class EscalationStatusRequest(BaseModel):
    status: str = Field(min_length=1)


class EscalationResponse(BaseModel):
    escalation_id: str
    session_id: str
    requester_role_id: str
    target_role_id: str
    subject: str
    detail: str
    status: str
    created_at_round: int

    @classmethod
    def of(cls, e: EscalationRequest) -> "EscalationResponse":
        return cls(
            escalation_id=e.escalation_id,
            session_id=e.session_id,
            requester_role_id=e.requester_role_id,
            target_role_id=e.target_role_id,
            subject=e.subject,
            detail=e.detail,
            status=e.status,
            created_at_round=e.created_at_round,
        )


@router.post("/{session_id}/escalations", response_model=EscalationResponse)
def raise_escalation(session_id: str, req: RaiseEscalationRequest) -> EscalationResponse:
    if not can_escalate(req.requester_role_id, req.target_role_id):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Role '{req.requester_role_id}' may not escalate to "
                f"'{req.target_role_id}' under the command hierarchy (ADR-0015)."
            ),
        )
    try:
        escalation = _service.raise_escalation(
            session_id=session_id,
            requester_role_id=req.requester_role_id,
            target_role_id=req.target_role_id,
            subject=req.subject,
            detail=req.detail,
            current_round=req.current_round,
        )
    except DomainRuleViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EscalationResponse.of(escalation)


@router.get("/{session_id}/escalations", response_model=list[EscalationResponse])
def list_escalations(
    session_id: str, role_id: str | None = Query(default=None)
) -> list[EscalationResponse]:
    return [EscalationResponse.of(e) for e in _service.list_for_session(session_id, role_id)]


@router.post(
    "/{session_id}/escalations/{escalation_id}/status", response_model=EscalationResponse
)
def set_escalation_status(
    session_id: str, escalation_id: str, req: EscalationStatusRequest
) -> EscalationResponse:
    try:
        updated = _service.set_status(session_id, escalation_id, req.status.strip().upper())
    except DomainRuleViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EscalationResponse.of(updated)
