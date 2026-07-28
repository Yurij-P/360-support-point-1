from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from tps360.api import dependencies
from tps360.api.dependencies import get_assessment_repo, get_community_repo
from tps360.assessment.domain.profile import CommunityPreparednessProfile
from tps360.assessment.services.profile_service import PreparednessProfileService
from tps360.core.domain.community_id import CommunityId
from tps360.core.exceptions import NotFoundError
from tps360.db.repositories import SQLAssessmentRepository, SQLCommunityRepository

router = APIRouter(
    prefix="/communities/{community_id}/preparedness-profile", tags=["preparedness-profiles"]
)
service = PreparednessProfileService()


@router.get("")
def get_profile(
    community_id: CommunityId,
    public: bool = False,
    community_repo: SQLCommunityRepository = Depends(get_community_repo),
    assessment_repo: SQLAssessmentRepository = Depends(get_assessment_repo),
) -> CommunityPreparednessProfile:
    try:
        community_repo.get(community_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))

    profile = dependencies.preparedness_profiles.get_by_community(community_id)

    if not profile:
        all_assessments = [a for a in assessment_repo.list_all() if a.community_id == community_id]
        latest_assessment = None
        if all_assessments:
            latest_assessment = max(all_assessments, key=lambda a: a.assessment_date)

        risks = dependencies.risks_registry.get(community_id, [])
        plan = dependencies.improvement_plans_registry.get(community_id)

        profile = service.generate_profile(community_id, latest_assessment, risks, plan)
        dependencies.preparedness_profiles.add(profile)

    if public:
        return service.generate_public_version(profile)
    return profile


@router.post("/agree")
def agree_profile(
    community_id: CommunityId,
    community_repo: SQLCommunityRepository = Depends(get_community_repo),
    assessment_repo: SQLAssessmentRepository = Depends(get_assessment_repo),
) -> CommunityPreparednessProfile:
    try:
        community_repo.get(community_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))

    profile = dependencies.preparedness_profiles.get_by_community(community_id)

    if not profile:
        all_assessments = [a for a in assessment_repo.list_all() if a.community_id == community_id]
        latest_assessment = None
        if all_assessments:
            latest_assessment = max(all_assessments, key=lambda a: a.assessment_date)

        risks = dependencies.risks_registry.get(community_id, [])
        plan = dependencies.improvement_plans_registry.get(community_id)

        profile = service.generate_profile(community_id, latest_assessment, risks, plan)
        dependencies.preparedness_profiles.add(profile)

    profile.agreed_by_community = True
    profile.agreed_at = datetime.now(timezone.utc)
    return dependencies.preparedness_profiles.save(profile)
