from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from tps360.api.dependencies import get_community_repo
from tps360.community.domain.passport_read_model import CommunityPassportReadModel
from tps360.community.services.catalog_service import (
    CommunityCatalogItem,
    CommunityCatalogService,
)
from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation, EntityNotFound, NotFoundError
from tps360.db.repositories import SQLCommunityRepository

router = APIRouter(prefix="/communities", tags=["communities"])
catalog_service = CommunityCatalogService()


class CatalogSearchResponse(BaseModel):
    items: list[CommunityCatalogItem]
    total_count: int


@router.get("/catalog", response_model=CatalogSearchResponse)
def get_communities_catalog(
    query: str | None = Query(default=None),
    region: str | None = Query(default=None),
    min_preparedness: float | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CatalogSearchResponse:
    items = catalog_service.search_catalog(
        query=query,
        region=region,
        min_preparedness=min_preparedness,
        limit=limit,
        offset=offset,
    )
    return CatalogSearchResponse(items=items, total_count=len(items))


@router.get("/{community_id}/passport", response_model=CommunityPassportReadModel)
def get_community_passport(community_id: str) -> CommunityPassportReadModel:
    try:
        return catalog_service.get_passport(community_id)
    except EntityNotFound as exc:
        raise HTTPException(404, str(exc))


@router.post("")
def create(
    item: Community, community_repo: SQLCommunityRepository = Depends(get_community_repo)
) -> Community:
    try:
        return community_repo.add(item)
    except DomainRuleViolation as exc:
        raise HTTPException(409, str(exc))


@router.get("/{community_id}")
def get(
    community_id: UUID, community_repo: SQLCommunityRepository = Depends(get_community_repo)
) -> Community:
    try:
        return community_repo.get(community_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))
