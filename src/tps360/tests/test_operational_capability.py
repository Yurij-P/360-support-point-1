from datetime import datetime
from uuid import uuid4

import pytest

from tps360.community_profile.domain import (
    OperationalCapability,
    Organization,
    ResourceInventoryItem,
)
from tps360.community_profile.domain.enums import (
    FacilityType,
    OrganizationType,
    ResourceType,
    VerificationStatus,
)
from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.geospatial.domain.enums import AccessLevel


def build_resource(**overrides: object) -> ResourceInventoryItem:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Generator",
        "resource_type": ResourceType.DIESEL_GENERATOR,
        "quantity": 1,
        "unit": "unit",
        "owner_organization_id": uuid4(),
        "storage_geo_feature_id": None,
        "availability_status": "available",
        "operational_status": "operational",
        "activation_time_minutes": 5,
        "technical_specifications": {},
        "required_operator_capabilities": (),
        "compatible_facility_ids": (),
        "consumables": {},
        "autonomy_hours": 10.0,
        "limitations": (),
        "access_level": AccessLevel.OPERATIONAL,
        "verification_status": VerificationStatus.VERIFIED,
        "last_verified_at": datetime(2026, 7, 24),
    }
    values.update(overrides)
    return ResourceInventoryItem(**values)  # type: ignore[arg-type]


def build_organization(**overrides: object) -> Organization:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Utility",
        "organization_type": OrganizationType.UTILITY,
        "status": VerificationStatus.VERIFIED,
        "contact_reference": None,
        "service_area": (),
        "geo_feature_id": None,
        "capabilities": (),
    }
    values.update(overrides)
    return Organization(**values)  # type: ignore[arg-type]


def build_capability(**overrides: object) -> OperationalCapability:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Emergency power",
        "required_resource_types": (ResourceType.DIESEL_GENERATOR,),
        "required_facility_types": (FacilityType.HEALTHCARE,),
        "required_organization_types": (OrganizationType.UTILITY,),
        "required_people": 2,
        "activation_time_minutes": 15,
        "operational_duration_hours": 8.0,
        "priority": 1,
        "is_available": False,
    }
    values.update(overrides)
    return OperationalCapability(**values)  # type: ignore[arg-type]


def test_valid_operational_capability() -> None:
    assert build_capability().name == "Emergency power"


def test_empty_name_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_capability(name=" ")


def test_negative_required_people_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_capability(required_people=-1)


def test_negative_activation_time_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_capability(activation_time_minutes=-1)


def test_negative_operational_duration_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_capability(operational_duration_hours=-1.0)


def test_negative_priority_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_capability(priority=-1)


def test_calculate_missing_resources_returns_missing_type() -> None:
    assert build_capability().calculate_missing_resources(()) == (ResourceType.DIESEL_GENERATOR,)


def test_calculate_missing_resources_uses_available_resource() -> None:
    assert build_capability().calculate_missing_resources((build_resource(),)) == ()


def test_calculate_missing_people_returns_shortfall() -> None:
    assert build_capability().calculate_missing_people(1) == 1


def test_calculate_missing_people_has_no_shortfall() -> None:
    assert build_capability().calculate_missing_people(2) == 0


def test_can_execute_with_all_required_inputs() -> None:
    assert build_capability().can_execute(
        (build_resource(),),
        (FacilityType.HEALTHCARE,),
        (build_organization(),),
        2,
    )


def test_calculate_availability_updates_state() -> None:
    capability = build_capability()

    assert capability.calculate_availability(
        (build_resource(),),
        (FacilityType.HEALTHCARE,),
        (build_organization(),),
        2,
    )
    assert capability.is_available