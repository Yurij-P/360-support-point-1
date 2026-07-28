from uuid import uuid4

import pytest

from tps360.core.domain.enums import HazardCategory
from tps360.core.domain.models import Hazard, Risk
from tps360.core.services import PreparednessService, RiskService


@pytest.mark.parametrize("value", [0, 1, 50, 99, 100])
def test_score_boundaries_are_classified(value: float) -> None:
    assert RiskService().classify_risk_level(value) in {"low", "moderate", "high", "critical"}


def test_preparedness_total_score_uses_dimensions() -> None:
    assert PreparednessService().calculate_total_score({"a": 20, "b": 40}) == 30


def test_risk_evidence_requires_non_empty_references() -> None:
    risk = Risk(
        community_id=str(uuid4()),
        hazard=Hazard(
            name="H",
            category=HazardCategory.CYBER,
            description="D",
            probability=1,
            potential_impact=1,
            geographic_scope="G",
        ),
        probability_score=1,
        impact_score=1,
        exposure_score=1,
        capability_modifier=1,
        confidence_level="low",
        evidence=[],
    )
    assert not RiskService().validate_evidence(risk)
