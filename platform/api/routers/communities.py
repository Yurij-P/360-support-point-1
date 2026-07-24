from uuid import UUID
from fastapi import APIRouter, HTTPException
from platform.core.domain.models import Community
from platform.core.exceptions import DomainRuleViolation, NotFoundError
from platform.api.dependencies import communities
router = APIRouter(prefix="/communities", tags=["communities"])
@router.post("")
def create(item: Community) -> Community:
    try: return communities.add(item)
    except DomainRuleViolation as exc: raise HTTPException(409, str(exc))
@router.get("/{community_id}")
def get(community_id: UUID) -> Community:
    try: return communities.get(community_id)
    except NotFoundError as exc: raise HTTPException(404, str(exc))
