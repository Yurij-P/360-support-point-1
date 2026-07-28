from fastapi import APIRouter

from tps360.core.domain.community_id import CommunityId
from tps360.core.domain.models import Risk
from tps360.core.services import RiskService

router = APIRouter(prefix="/communities/{community_id}/risks", tags=["risks"])


@router.post("")
def create(community_id: CommunityId, risk: Risk) -> Risk:
    risk.community_id = community_id
    risk.overall_score = RiskService().calculate_risk(risk)
    return risk
