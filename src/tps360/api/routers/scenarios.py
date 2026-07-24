from uuid import UUID
from fastapi import APIRouter, HTTPException
from tps360.api.dependencies import scenarios
from tps360.core.domain.models import Scenario
from tps360.core.exceptions import NotFoundError
router = APIRouter(prefix="/scenarios", tags=["scenarios"])
@router.post("")
def create(item: Scenario) -> Scenario: return scenarios.add(item)
@router.get("/{scenario_id}")
def get(scenario_id: UUID) -> Scenario:
    try: return scenarios.get(scenario_id)
    except NotFoundError as exc: raise HTTPException(404, str(exc))
