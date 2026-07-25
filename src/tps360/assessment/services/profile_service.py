from typing import Any
from uuid import UUID

from tps360.assessment.domain.profile import CommunityPreparednessProfile
from tps360.core.domain.models import ImprovementPlan, PreparednessAssessment, Risk


class PreparednessProfileService:
    def generate_profile(
        self,
        community_id: UUID,
        assessment: PreparednessAssessment | None,
        risks: list[Risk],
        improvement_plan: ImprovementPlan | None,
    ) -> CommunityPreparednessProfile:
        strengths = []
        gaps = []
        evidence = []

        if assessment:
            for dim, score in assessment.dimensions.items():
                if score >= 70.0:
                    strengths.append(dim)
                elif score < 40.0:
                    gaps.append(dim)
            if assessment.evidence:
                evidence.extend(assessment.evidence)

        profile_risks = []
        for r in risks:
            score = r.overall_score or 0.0
            if score > 50.0:
                profile_risks.append({
                    "hazard_name": r.hazard.name,
                    "overall_score": score,
                    "confidence_level": r.confidence_level,
                })
            if r.evidence:
                evidence.extend(r.evidence)

        improvement_priorities = []
        if improvement_plan:
            for action in improvement_plan.actions:
                if action.priority <= 2 and action.status != "completed":
                    improvement_priorities.append(action.title)
            if improvement_plan.indicators:
                evidence.extend(improvement_plan.indicators)

        evidence = sorted(list(set(evidence)))

        if len(evidence) >= 5:
            confidence = "HIGH"
        elif len(evidence) >= 2:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return CommunityPreparednessProfile(
            community_id=community_id,
            assessment_id=assessment.id if assessment else None,
            strengths=strengths,
            gaps=gaps,
            evidence=evidence,
            risks=profile_risks,
            improvement_priorities=improvement_priorities,
            confidence_level=confidence,
            is_public=False,
        )

    def generate_public_version(
        self, profile: CommunityPreparednessProfile
    ) -> CommunityPreparednessProfile:
        public_risks = [
            {"hazard_name": r["hazard_name"], "confidence_level": r["confidence_level"]}
            for r in profile.risks
        ]
        public_evidence = [
            f"Verified evidence document #{i+1}" for i in range(len(profile.evidence))
        ]

        return CommunityPreparednessProfile(
            id=profile.id,
            community_id=profile.community_id,
            assessment_id=profile.assessment_id,
            strengths=profile.strengths,
            gaps=profile.gaps,
            evidence=public_evidence,
            risks=public_risks,
            improvement_priorities=profile.improvement_priorities,
            confidence_level=profile.confidence_level,
            version=profile.version,
            is_public=True,
            agreed_by_community=profile.agreed_by_community,
            agreed_at=profile.agreed_at,
        )
