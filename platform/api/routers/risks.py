from uuid import UUID
from fastapi import APIRouter
from platform.core.domain.models import Risk
from platform.core.services import RiskService
router = APIRouter(prefix="/communities/{community_id}/risks", tags=["risks"])
@router.post("")
def create(community_id: UUID, risk: Risk) -> Risk:
    risk.community_id = community_id; risk.overall_score = RiskService().calculate_risk(risk); return risk
