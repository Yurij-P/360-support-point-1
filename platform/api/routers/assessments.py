from uuid import UUID
from fastapi import APIRouter
from platform.api.dependencies import assessments
from platform.core.domain.models import PreparednessAssessment
from platform.core.services import PreparednessService
router = APIRouter(prefix="/communities/{community_id}/assessments", tags=["assessments"])
@router.post("")
def create(community_id: UUID, item: PreparednessAssessment) -> PreparednessAssessment:
    service=PreparednessService(); item.community_id=community_id; item.total_score=service.calculate_total_score(item.dimensions); item.maturity_level=service.determine_maturity_level(item.total_score); return assessments.add(item)
