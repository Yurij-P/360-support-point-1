from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from tps360.community.services.catalog_service import CommunityCatalogService
from tps360.core.exceptions import EntityNotFound
from tps360.simulation.services.scenario_catalog_service import (
    ScenarioCatalogService,
    ScenarioCompatibilityResult,
    ScenarioTemplateCatalogItem,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])
scenario_service = ScenarioCatalogService()
community_catalog = CommunityCatalogService()


class CompatibilityCheckRequest(BaseModel):
    scenario_id: str
    community_id: str


class ScenariosCatalogResponse(BaseModel):
    items: list[ScenarioTemplateCatalogItem]
    total_count: int


@router.get("/catalog", response_model=ScenariosCatalogResponse)
def get_scenarios_catalog(
    threat_category: str | None = Query(default=None),
) -> ScenariosCatalogResponse:
    items = scenario_service.list_scenarios(threat_category=threat_category)
    return ScenariosCatalogResponse(items=items, total_count=len(items))


@router.post("/compatibility-check", response_model=ScenarioCompatibilityResult)
def check_scenario_compatibility(
    req: CompatibilityCheckRequest,
) -> ScenarioCompatibilityResult:
    try:
        passport = community_catalog.get_passport(req.community_id)
        return scenario_service.evaluate_compatibility(req.scenario_id, passport)
    except EntityNotFound as exc:
        raise HTTPException(404, str(exc))
