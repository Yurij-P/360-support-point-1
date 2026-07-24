from uuid import UUID

import pytest

from tps360.community_profile.domain import Settlement
from tps360.community_profile.domain.enums import VerificationStatus
from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.community_profile.value_objects import PopulationCount


def test_settlement_creation() -> None:
    settlement = Settlement(
        name="Львів",
        settlement_type="city",
        population=PopulationCount(717273),
        starosta_district="Central",
        geo_feature_id=UUID("12345678-1234-5678-1234-567812345678"),
        verification_status=VerificationStatus.VERIFIED,
        evidence=("registry",),
    )

    assert settlement.name == "Львів"
    assert settlement.population == PopulationCount(717273)
    assert settlement.geo_feature_id == UUID("12345678-1234-5678-1234-567812345678")
    assert settlement.id.version == 4


def test_empty_settlement_name_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        Settlement(name="   ", settlement_type="village", population=PopulationCount(1))


def test_empty_settlement_type_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        Settlement(name="Борщів", settlement_type="  ", population=PopulationCount(1))


def test_empty_evidence_item_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        Settlement(
            name="Борщів",
            settlement_type="village",
            population=PopulationCount(1),
            evidence=("registry", " "),
        )
