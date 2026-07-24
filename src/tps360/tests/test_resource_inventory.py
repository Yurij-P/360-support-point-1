from datetime import datetime
from uuid import UUID, uuid4

import pytest

from tps360.community_profile.domain import ResourceInventoryItem
from tps360.community_profile.domain.enums import ResourceType, VerificationStatus
from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.geospatial.domain.enums import AccessLevel


def build_resource(**overrides: object) -> ResourceInventoryItem:
    facility_id = UUID("12345678-1234-5678-1234-567812345678")
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Mobile generator",
        "resource_type": ResourceType.DIESEL_GENERATOR,
        "quantity": 1,
        "unit": "unit",
        "owner_organization_id": uuid4(),
        "storage_geo_feature_id": None,
        "availability_status": "available",
        "operational_status": "operational",
        "activation_time_minutes": 10,
        "technical_specifications": {"consumption_per_hour": 2.0},
        "required_operator_capabilities": ("generator operation",),
        "compatible_facility_ids": (facility_id,),
        "consumables": {"diesel": 20.0},
        "autonomy_hours": None,
        "limitations": ("outdoor use",),
        "access_level": AccessLevel.OPERATIONAL,
        "verification_status": VerificationStatus.VERIFIED,
        "last_verified_at": datetime(2026, 7, 24),
        "evidence": ("registry",),
    }
    values.update(overrides)
    return ResourceInventoryItem(**values)  # type: ignore[arg-type]


def test_valid_resource() -> None:
    resource = build_resource()

    assert resource.is_available()


def test_negative_quantity_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_resource(quantity=-1)


def test_empty_unit_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_resource(unit=" ")


def test_negative_activation_time_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_resource(activation_time_minutes=-1)


def test_negative_autonomy_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_resource(autonomy_hours=-1.0)


def test_duplicate_facility_ids_raise_error() -> None:
    facility_id = UUID("12345678-1234-5678-1234-567812345678")

    with pytest.raises(ProfileRuleViolation):
        build_resource(compatible_facility_ids=(facility_id, facility_id))


def test_negative_consumable_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_resource(consumables={"diesel": -1.0})


def test_requires_operator() -> None:
    assert build_resource().requires_operator()


def test_supports_facility() -> None:
    facility_id = UUID("12345678-1234-5678-1234-567812345678")

    assert build_resource().supports_facility(facility_id)


def test_estimated_operational_hours() -> None:
    assert build_resource().estimated_operational_hours({"diesel": 12.0}) == 6.0