from uuid import UUID

from fastapi import APIRouter, Depends

from tps360.api.dependencies import get_assessment_repo
from tps360.core.domain.models import PreparednessAssessment
from tps360.core.services import PreparednessService
from tps360.db.repositories import SQLAssessmentRepository

router = APIRouter(prefix="/communities/{community_id}/assessments", tags=["assessments"])


@router.post("")
def create(
    community_id: UUID,
    item: PreparednessAssessment,
    assessment_repo: SQLAssessmentRepository = Depends(get_assessment_repo),
) -> PreparednessAssessment:
    service = PreparednessService()
    item.community_id = community_id
    item.total_score = service.calculate_total_score(item.dimensions)
    item.maturity_level = service.determine_maturity_level(item.total_score)
    return assessment_repo.add(item)
