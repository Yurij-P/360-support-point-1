from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tps360.api import dependencies
from tps360.api.main import app
from tps360.assessment.domain.profile import CommunityPreparednessProfile
from tps360.assessment.services.profile_service import PreparednessProfileService
from tps360.core.domain.enums import HazardCategory
from tps360.core.domain.models import (
    Community,
    Hazard,
    ImprovementAction,
    ImprovementPlan,
    PreparednessAssessment,
    Risk,
)

client = TestClient(app)


def test_profile_generation():
    service = PreparednessProfileService()
    community_id = uuid4()

    # 1. Create a mock assessment
    assessment = PreparednessAssessment(
        community_id=community_id,
        assessment_date=date(2026, 7, 25),
        dimensions={
            "governance": 85.0,  # Strength
            "planning": 35.0,  # Gap
            "coordination": 50.0,  # Neutral
        },
        evidence=["evidence_doc_1", "evidence_doc_2"],
        assessor="Test Assessor",
        confidence_level="HIGH",
    )

    # 2. Create mock risks
    risks = [
        Risk(
            community_id=community_id,
            hazard=Hazard(
                name="Flood",
                category=HazardCategory.NATURAL,
                description="High risk of seasonal flooding",
                probability=80.0,
                potential_impact=80.0,
                geographic_scope="Regional",
            ),
            probability_score=80.0,
            impact_score=80.0,
            exposure_score=80.0,
            capability_modifier=10.0,
            overall_score=75.0,  # Active Risk (>50)
            confidence_level="HIGH",
            evidence=["risk_evidence_1"],
        ),
        Risk(
            community_id=community_id,
            hazard=Hazard(
                name="Cyber Attack",
                category=HazardCategory.CYBER,
                description="Low risk cyber threat",
                probability=20.0,
                potential_impact=30.0,
                geographic_scope="Local",
            ),
            probability_score=20.0,
            impact_score=30.0,
            exposure_score=20.0,
            capability_modifier=0.0,
            overall_score=25.0,  # Inactive Risk (<50)
            confidence_level="LOW",
            evidence=["risk_evidence_2"],
        ),
    ]

    # 3. Create a mock improvement plan
    plan = ImprovementPlan(
        community_id=community_id,
        source_assessment_id=assessment.id,
        actions=[
            ImprovementAction(title="Action 1 - High Priority", priority=1, status="open"),
            ImprovementAction(title="Action 2 - Med Priority", priority=2, status="open"),
            ImprovementAction(title="Action 3 - Low Priority", priority=4, status="open"),
            ImprovementAction(
                title="Action 4 - High Priority Completed", priority=1, status="completed"
            ),
        ],
        indicators=["plan_indicator_1"],
    )

    # Generate Profile
    profile = service.generate_profile(community_id, assessment, risks, plan)

    # Asserts
    assert profile.community_id == community_id
    assert profile.assessment_id == assessment.id
    assert "governance" in profile.strengths
    assert "planning" in profile.gaps
    assert "coordination" not in profile.strengths
    assert "coordination" not in profile.gaps

    # Check evidence deduplication
    assert "evidence_doc_1" in profile.evidence
    assert "risk_evidence_1" in profile.evidence
    assert "risk_evidence_2" in profile.evidence
    assert "plan_indicator_1" in profile.evidence

    # Check risks (only Flood should be included as overall_score > 50)
    assert len(profile.risks) == 1
    assert profile.risks[0]["hazard_name"] == "Flood"
    assert profile.risks[0]["overall_score"] == 75.0

    # Check priorities (priority <= 2, status != "completed")
    assert "Action 1 - High Priority" in profile.improvement_priorities
    assert "Action 2 - Med Priority" in profile.improvement_priorities
    assert "Action 3 - Low Priority" not in profile.improvement_priorities
    assert "Action 4 - High Priority Completed" not in profile.improvement_priorities

    # Check confidence level calculation (>=5 evidence docs -> HIGH)
    assert profile.confidence_level == "HIGH"


def test_public_profile_redaction():
    service = PreparednessProfileService()
    community_id = uuid4()

    profile = CommunityPreparednessProfile(
        community_id=community_id,
        strengths=["governance"],
        gaps=["planning"],
        evidence=["doc1", "doc2"],
        risks=[{"hazard_name": "Flood", "overall_score": 75.0, "confidence_level": "HIGH"}],
        improvement_priorities=["action1"],
        confidence_level="MEDIUM",
    )

    public_profile = service.generate_public_version(profile)

    assert public_profile.is_public is True
    # Risks should not contain specific scores in public view
    assert "overall_score" not in public_profile.risks[0]
    assert public_profile.risks[0]["hazard_name"] == "Flood"

    # Evidence should be anonymized
    assert len(public_profile.evidence) == 2
    assert "doc1" not in public_profile.evidence
    assert public_profile.evidence[0] == "Verified evidence document #1"


def test_api_endpoints():
    # 1. Clean registries
    dependencies.communities.items.clear()
    dependencies.assessments.items.clear()
    dependencies.preparedness_profiles.items.clear()
    dependencies.risks_registry.clear()
    dependencies.improvement_plans_registry.clear()

    # 2. Add community
    community_id = uuid4()
    community = Community(
        id=community_id, name="Test Community", code="TC1", oblast="Kyiv", population=100, area_km2=10
    )
    dependencies.communities.add(community)

    # 3. Create active assessment
    assessment = PreparednessAssessment(
        community_id=community_id,
        assessment_date=date(2026, 7, 25),
        dimensions={"governance": 80.0},
        evidence=["doc_a"],
        assessor="Assessor A",
        confidence_level="MEDIUM",
    )
    dependencies.assessments.add(assessment)

    # Call API to get profile (triggers dynamic generation)
    resp = client.get(f"/communities/{community_id}/preparedness-profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["community_id"] == str(community_id)
    assert "governance" in data["strengths"]
    assert data["is_public"] is False

    # Get public profile
    resp_pub = client.get(f"/communities/{community_id}/preparedness-profile?public=true")
    assert resp_pub.status_code == 200
    data_pub = resp_pub.json()
    assert data_pub["is_public"] is True
    assert data_pub["evidence"][0] == "Verified evidence document #1"

    # Agree to profile
    resp_agree = client.post(f"/communities/{community_id}/preparedness-profile/agree")
    assert resp_agree.status_code == 200
    data_agree = resp_agree.json()
    assert data_agree["agreed_by_community"] is True
    assert data_agree["agreed_at"] is not None

    # Get profile for non-existent community should return 404
    resp_fake = client.get(f"/communities/{uuid4()}/preparedness-profile")
    assert resp_fake.status_code == 404
