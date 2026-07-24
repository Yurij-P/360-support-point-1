from uuid import UUID, uuid4

import pytest

from tps360.community_profile.domain import VulnerableGroup
from tps360.community_profile.domain.enums import VerificationStatus
from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.community_profile.value_objects import PopulationCount


def build_group(**overrides: object) -> VulnerableGroup:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")
    organization_id = UUID("87654321-4321-8765-4321-876543218765")
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Older residents",
        "category": "age",
        "estimated_count": PopulationCount(20),
        "geographic_scope": (settlement_id,),
        "support_needs": ("medication",),
        "responsible_organization_ids": (organization_id,),
        "verification_status": VerificationStatus.VERIFIED,
        "evidence": ("registry",),
    }
    values.update(overrides)
    return VulnerableGroup(**values)  # type: ignore[arg-type]


def test_valid_group() -> None:
    group = build_group()

    assert group.name == "Older residents"
    assert group.estimated_count == PopulationCount(20)


def test_empty_name_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_group(name=" ")


def test_empty_category_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_group(category=" ")


def test_duplicate_geographic_scope_raises_error() -> None:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")

    with pytest.raises(ProfileRuleViolation):
        build_group(geographic_scope=(settlement_id, settlement_id))


def test_duplicate_responsible_organizations_raises_error() -> None:
    organization_id = UUID("87654321-4321-8765-4321-876543218765")

    with pytest.raises(ProfileRuleViolation):
        build_group(responsible_organization_ids=(organization_id, organization_id))


def test_contains_settlement() -> None:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")

    assert build_group().contains_settlement(settlement_id)