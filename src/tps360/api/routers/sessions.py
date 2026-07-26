from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from secrets import token_urlsafe
from typing import Any, TypeVar
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from tps360.api.dependencies import sessions
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.simulation.domain.decision_payload import validate_decision_payload
from tps360.simulation.domain.session import (
    FacilitatedSession,
    Participant,
    ParticipantDecision,
    RoleProfile,
    SessionInject,
    SessionJournalEntry,
    SessionStatus,
)
from tps360.simulation.services import (
    AARTelemetryService,
    AfterActionReviewReport,
    CrisisLifecycleProjectionVariant,
    FacilitatorConsoleReadModel,
    FacilitatorConsoleService,
    LegoDecisionCard,
    LobbyParticipantStatus,
    LobbyRoomStatus,
    ParticipantExperienceRecord,
    ResourceTransferDirective,
    RoleDashboardService,
    RoleWorkspaceReadModel,
    RoundTelemetrySnapshot,
    SessionLobbyService,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])
T = TypeVar("T")
lobby_service = SessionLobbyService()
role_dashboard_service = RoleDashboardService()
facilitator_console_service = FacilitatorConsoleService()
aar_telemetry_service = AARTelemetryService()




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


class AssignLobbyRoleRequest(BaseModel):
    participant_id: str
    role_id: str


class JoinLobbyRequest(BaseModel):
    display_name: str = Field(min_length=1)


class SubmitLegoCardRequest(BaseModel):
    role_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    target_facility_id: str = Field(min_length=1)
    allocated_resources: dict[str, Decimal] = Field(default_factory=dict)
    allocated_personnel: int = Field(default=0, ge=0)
    custom_instructions: str = ""


class TransferResourcesRequest(BaseModel):
    sender_role_id: str = Field(min_length=1)
    recipient_role_id: str = Field(min_length=1)
    resources: dict[str, Decimal] = Field(default_factory=dict)
    authorization_note: str = ""


class SendInjectRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class SubmitDecisionRequest(BaseModel):
    participant_id: UUID | None = None
    decision_payload: dict[str, Any]


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
    # Initialize lobby room for pre-start standby waiting
    lobby_service.create_room(session_id=str(session.id), capacity=request.player_capacity)

    return CreateSessionResponse(
        **session.model_dump(),
        facilitator_token=facilitator_token,
        join_token=join_token,
    )


@router.post("/{session_id}/lobby/join", response_model=LobbyParticipantStatus)
def join_lobby(session_id: str, req: JoinLobbyRequest) -> LobbyParticipantStatus:
    try:
        return lobby_service.join_standby_room(session_id=session_id, display_name=req.display_name)
    except DomainRuleViolation as exc:
        raise HTTPException(409, str(exc))


@router.post("/{session_id}/lobby/assign-role", response_model=LobbyParticipantStatus)
def assign_lobby_role(session_id: str, req: AssignLobbyRoleRequest) -> LobbyParticipantStatus:
    try:
        return lobby_service.assign_participant_role(
            session_id=session_id, participant_id=req.participant_id, role_id=req.role_id
        )
    except DomainRuleViolation as exc:
        raise HTTPException(409, str(exc))


@router.get("/{session_id}/lobby-status", response_model=LobbyRoomStatus)
def get_lobby_status(session_id: str) -> LobbyRoomStatus:
    return lobby_service.get_lobby_status(session_id)


@router.get("/{session_id}/role-workspace", response_model=RoleWorkspaceReadModel)
def get_role_workspace(session_id: str, role_id: str = Query(...)) -> RoleWorkspaceReadModel:
    return role_dashboard_service.get_role_workspace(session_id=session_id, role_id=role_id)


@router.get("/{session_id}/facilitator-console", response_model=FacilitatorConsoleReadModel)
def get_facilitator_console(
    session_id: str,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> FacilitatorConsoleReadModel:
    return facilitator_console_service.get_facilitator_console(session_id=session_id)


@router.get("/{session_id}/future-projections", response_model=list[CrisisLifecycleProjectionVariant])
def get_future_projections(
    session_id: str,
    crisis_type: str = Query(default="Ракетно-дроновий обстріл та детонація БК"),
    current_round: int = Query(default=1, ge=1),
) -> list[CrisisLifecycleProjectionVariant]:
    projections = facilitator_console_service.generate_5_future_lifecycle_variants(
        session_id=session_id, crisis_type=crisis_type, current_round=current_round
    )
    return list(projections)


class ApproveAIProposalRequest(BaseModel):
    variant_id: str = Field(min_length=1)
    custom_title: str | None = None
    custom_description: str | None = None


@router.post("/{session_id}/injects/approve-ai-proposal")
def approve_ai_proposal(
    session_id: str,
    req: ApproveAIProposalRequest,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> dict[str, Any]:
    try:
        return facilitator_console_service.approve_ai_proposal(
            session_id=session_id,
            variant_id=req.variant_id,
            custom_title=req.custom_title,
            custom_description=req.custom_description,
        )
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))


class InjectPsychologicalFrictionRequest(BaseModel):

    target_role_id: str = Field(min_length=1)
    friction_type: str = Field(min_length=1)  # AIR_RAID_SIREN, URGENT_PHONE_CALL, SOCIAL_MEDIA_TROLLING, PUBLIC_PROTEST, STAFF_INCIDENT, FACILITATOR_CUSTOM_FRICTION
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    stress_level_delta: float = Field(default=15.0, ge=0.0, le=100.0)
    audio_siren_signal: bool = Field(default=False)
    current_round: int = Field(default=1, ge=1)


@router.post("/{session_id}/injects/psychological-friction")
def inject_psychological_friction(
    session_id: str,
    req: InjectPsychologicalFrictionRequest,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> Any:
    return role_dashboard_service.inject_psychological_friction(
        session_id=session_id,
        target_role_id=req.target_role_id,
        friction_type=req.friction_type,
        title=req.title,
        description=req.description,
        stress_level_delta=req.stress_level_delta,
        audio_siren_signal=req.audio_siren_signal,
        current_round=req.current_round,
    )



@router.post("/{session_id}/rounds/advance")
def advance_round(
    session_id: str,
    current_round: int = Query(default=1, ge=1),
    mitigation_score_pct: float = Query(default=0.0, ge=0.0, le=100.0),
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> dict[str, Any]:
    # Resolve pending LEGO decisions execution in round
    role_dashboard_service.resolve_round_execution(session_id=session_id, round_number=current_round)
    return facilitator_console_service.advance_session_round(
        session_id=session_id,
        current_round=current_round,
        mitigation_score_pct=mitigation_score_pct,
    )





@router.post("/{session_id}/lego-decisions", response_model=LegoDecisionCard)
def submit_lego_decision(session_id: str, req: SubmitLegoCardRequest) -> LegoDecisionCard:
    try:
        return role_dashboard_service.submit_lego_decision_card(
            session_id=session_id,
            role_id=req.role_id,
            action_type=req.action_type,
            target_facility_id=req.target_facility_id,
            allocated_resources=req.allocated_resources,
            allocated_personnel=req.allocated_personnel,
            custom_instructions=req.custom_instructions,
        )
    except DomainRuleViolation as exc:
        raise HTTPException(409, str(exc))


@router.post("/{session_id}/resource-transfers", response_model=ResourceTransferDirective)
def transfer_resources_oms(
    session_id: str, req: TransferResourcesRequest
) -> ResourceTransferDirective:
    try:
        return role_dashboard_service.transfer_resources_oms(
            session_id=session_id,
            sender_role_id=req.sender_role_id,
            recipient_role_id=req.recipient_role_id,
            resources=req.resources,
            authorization_note=req.authorization_note,
        )
    except DomainRuleViolation as exc:
        raise HTTPException(409, str(exc))


class ParticipantInjectResponse(BaseModel):
    id: UUID
    title: str
    description: str
    sent_at: datetime


class ParticipantViewResponse(BaseModel):
    participant_id: UUID
    display_name: str
    lifecycle: str
    reconnect_status: str
    role_assigned: bool
    role_id: UUID | None
    role_profile: RoleProfile | None
    session_status: SessionStatus
    injects: list[ParticipantInjectResponse] = Field(default_factory=list)
    decisions: list[ParticipantDecision] = Field(default_factory=list)


class ParticipantJoinResponse(ParticipantViewResponse):
    participant_token: str | None


@router.get("/{session_id}")
def get_session(
    session_id: UUID,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> SessionResponse:
    session = item(session_id)
    authorize_facilitator(session, facilitator_token)
    return SessionResponse.from_domain(session)


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
        injects=participant_visible_injects(session, participant),
        decisions=participant_decisions(session, participant),
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
        injects=participant_visible_injects(session, participant),
        decisions=participant_decisions(session, participant),
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
    participant_token: str | None = Header(None, alias="X-Participant-Token"),
) -> ParticipantDecision:
    session = item(session_id)
    participant = authorize_participant(session, participant_token)
    if request.participant_id is not None and request.participant_id != participant.id:
        raise HTTPException(403, "Participant token does not match participant_id")
    inject = domain_action(lambda: session._inject(inject_id))
    if not participant_can_access_inject(participant, inject):
        raise HTTPException(403, "Inject is not available to this participant")
    try:
        decision_payload = validate_decision_payload(request.decision_payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return domain_action(
        lambda: session.submit_decision(
            inject_id,
            participant.id,
            decision_payload,
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
def get_journal(
    session_id: UUID,
    facilitator_token: str | None = Header(None, alias="X-Facilitator-Token"),
) -> list[SessionJournalEntry]:
    session = item(session_id)
    authorize_facilitator(session, facilitator_token)
    return session.journal


def participant_visible_injects(
    session: FacilitatedSession, participant: Participant
) -> list[ParticipantInjectResponse]:
    return [
        ParticipantInjectResponse(
            id=inject.id,
            title=inject.title,
            description=inject.description,
            sent_at=inject.sent_at,
        )
        for inject in session.injects
        if participant_can_access_inject(participant, inject)
    ]


def participant_decisions(
    session: FacilitatedSession, participant: Participant
) -> list[ParticipantDecision]:
    return [
        decision
        for decision in session.decisions
        if decision.participant_id == participant.id
    ]


def participant_can_access_inject(participant: Participant, inject: SessionInject) -> bool:
    payload = inject.payload or {}
    role_targets = payload.get("target_role_ids") or payload.get("target_roles") or []
    participant_targets = payload.get("target_participant_ids") or []
    if participant_targets and str(participant.id) not in {
        str(target) for target in participant_targets
    }:
        return False
    if role_targets and str(participant.role_id) not in {str(target) for target in role_targets}:
        return False
    return True


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


@router.get("/{session_id}/aar-report", response_model=AfterActionReviewReport)
def get_aar_report(session_id: str) -> AfterActionReviewReport:
    return aar_telemetry_service.generate_aar_report(session_id=session_id)


@router.get("/{session_id}/telemetry", response_model=list[RoundTelemetrySnapshot])
def get_session_telemetry(session_id: str) -> list[RoundTelemetrySnapshot]:
    return list(aar_telemetry_service.get_session_telemetry(session_id=session_id))


@router.get("/participants/{participant_id}/experience-record", response_model=ParticipantExperienceRecord)
def get_participant_experience(participant_id: str) -> ParticipantExperienceRecord:
    rec = aar_telemetry_service.get_participant_experience(participant_id)
    if not rec:
        return aar_telemetry_service.record_participant_experience(
            participant_id=participant_id, community_id="verkhovyna"
        )
    return rec

