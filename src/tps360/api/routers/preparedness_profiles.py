from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException

from tps360.api import dependencies
from tps360.assessment.domain.profile import CommunityPreparednessProfile
from tps360.assessment.services.profile_service import PreparednessProfileService
from tps360.core.exceptions import NotFoundError

router = APIRouter(
    prefix="/communities/{community_id}/preparedness-profile", tags=["preparedness-profiles"]
)
service = PreparednessProfileService()


@router.get("")
def get_profile(community_id: UUID, public: bool = False) -> CommunityPreparednessProfile:
    try:
        dependencies.communities.get(community_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))

    profile = dependencies.preparedness_profiles.get_by_community(community_id)

    if not profile:
        # Find latest assessment
        all_assessments = [
            a for a in dependencies.assessments.items.values() if a.community_id == community_id
        ]
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
def agree_profile(community_id: UUID) -> CommunityPreparednessProfile:
    try:
        dependencies.communities.get(community_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))

    profile = dependencies.preparedness_profiles.get_by_community(community_id)

    if not profile:
        # Generate dynamic first if none exists
        all_assessments = [
            a for a in dependencies.assessments.items.values() if a.community_id == community_id
        ]
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
