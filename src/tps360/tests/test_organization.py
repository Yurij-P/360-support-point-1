from uuid import UUID, uuid4

import pytest

from tps360.community_profile.domain import Organization
from tps360.community_profile.domain.enums import OrganizationType, VerificationStatus
from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.community_profile.value_objects import ContactReference


def build_organization(**overrides: object) -> Organization:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Community Hospital",
        "organization_type": OrganizationType.HEALTHCARE,
        "status": VerificationStatus.VERIFIED,
        "contact_reference": ContactReference("secret:1", "Reception", "restricted"),
        "service_area": (settlement_id,),
        "geo_feature_id": UUID("87654321-4321-8765-4321-876543218765"),
        "capabilities": ("emergency care",),
        "evidence": ("registry",),
    }
    values.update(overrides)
    return Organization(**values)  # type: ignore[arg-type]


def test_valid_organization() -> None:
    organization = build_organization()

    assert organization.name == "Community Hospital"
    assert organization.organization_type is OrganizationType.HEALTHCARE


def test_empty_name_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_organization(name=" ")


def test_duplicate_service_area_raises_error() -> None:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")

    with pytest.raises(ProfileRuleViolation):
        build_organization(service_area=(settlement_id, settlement_id))


def test_empty_capability_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_organization(capabilities=(" ",))


def test_serves() -> None:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")

    assert build_organization().serves(settlement_id)


def test_has_capability() -> None:
    assert build_organization().has_capability("emergency care")