from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from tps360.api.dependencies import get_session_repo
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.db.repositories import SQLSessionRepository
from tps360.simulation.services.role_catalog_service import RoleCatalogEntry, RoleCatalogService

router = APIRouter(tags=["roles"])
_catalog_service = RoleCatalogService()


class RoleCatalogEntryResponse(BaseModel):
    role_id: str
    position: str
    category: str
    category_key: str

    @classmethod
    def from_entry(cls, entry: RoleCatalogEntry) -> "RoleCatalogEntryResponse":
        return cls(role_id=entry.role_id, position=entry.position, category=entry.category, category_key=entry.category_key)


class RoleCatalogResponse(BaseModel):
    total: int
    categories: int
    items: list[RoleCatalogEntryResponse]


class ParticipantRoleView(BaseModel):
    role_id: UUID
    title: str
    category: str
    briefing: str
    allowed_actions: list[str]
    visibility_rules: list[str]
    lifecycle: str


@router.get("/roles/catalog", response_model=RoleCatalogResponse)
def get_role_catalog(category_key: str | None = None) -> RoleCatalogResponse:
    entries = _catalog_service.list_entries(category_key=category_key)
    items = [RoleCatalogEntryResponse.from_entry(e) for e in entries]
    return RoleCatalogResponse(total=len(items), categories=len({e.category_key for e in entries}), items=items)


@router.get("/roles/catalog/{role_id}", response_model=RoleCatalogEntryResponse)
def get_role_catalog_entry(role_id: str) -> RoleCatalogEntryResponse:
    entry = _catalog_service.get_entry(role_id)
    if entry is None:
        raise HTTPException(404, f"Role '{role_id}' not found in catalog.")
    return RoleCatalogEntryResponse.from_entry(entry)


@router.get("/sessions/{session_id}/roles/me", response_model=ParticipantRoleView)
def get_my_role(
    session_id: UUID,
    participant_token: str | None = Header(None, alias="X-Participant-Token"),
    session_repo: SQLSessionRepository = Depends(get_session_repo),
) -> ParticipantRoleView:
    if not participant_token:
        raise HTTPException(401, "X-Participant-Token header is required.")
    try:
        session = session_repo.get(session_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    try:
        participant = session.participant_for_token(participant_token)
    except DomainRuleViolation as exc:
        raise HTTPException(401, str(exc)) from exc
    if participant.role_id is None:
        raise HTTPException(403, "No role has been assigned to this participant yet.")
    profile = session.role_profile(participant.role_id)
    if profile is None:
        raise HTTPException(404, "Assigned role profile not found in this session.")
    return ParticipantRoleView(
        role_id=profile.role_id,
        title=profile.title,
        category=profile.category,
        briefing=profile.briefing,
        allowed_actions=profile.allowed_actions,
        visibility_rules=profile.visibility_rules,
        lifecycle=participant.lifecycle.value,
    )
