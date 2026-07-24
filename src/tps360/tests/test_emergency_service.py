from uuid import UUID, uuid4

import pytest

from tps360.community_profile.domain import EmergencyService
from tps360.community_profile.domain.enums import OrganizationType, VerificationStatus
from tps360.community_profile.exceptions import ProfileRuleViolation


def build_service(**overrides: object) -> EmergencyService:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")
    values: dict[str, object] = {
        "id": uuid4(),
        "organization_id": uuid4(),
        "service_type": OrganizationType.EMERGENCY_SERVICE,
        "operational_status": "operational",
        "availability_24_7": True,
        "response_time_minutes": 15,
        "personnel_count": 12,
        "vehicle_count": 3,
        "service_area": (settlement_id,),
        "geo_feature_id": None,
        "capabilities": ("rescue",),
        "verification_status": VerificationStatus.VERIFIED,
        "evidence": ("registry",),
    }
    values.update(overrides)
    return EmergencyService(**values)  # type: ignore[arg-type]


def test_valid_emergency_service() -> None:
    service = build_service()

    assert service.response_time_minutes == 15
    assert service.personnel_count == 12


def test_negative_response_time_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_service(response_time_minutes=-1)


def test_negative_personnel_or_vehicle_count_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_service(personnel_count=-1)
    with pytest.raises(ProfileRuleViolation):
        build_service(vehicle_count=-1)


def test_duplicate_service_area_or_empty_text_raises_error() -> None:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")

    with pytest.raises(ProfileRuleViolation):
        build_service(service_area=(settlement_id, settlement_id))
    with pytest.raises(ProfileRuleViolation):
        build_service(capabilities=(" ",))
    with pytest.raises(ProfileRuleViolation):
        build_service(evidence=(" ",))


def test_serves() -> None:
    settlement_id = UUID("12345678-1234-5678-1234-567812345678")

    assert build_service().serves(settlement_id)


def test_is_available() -> None:
    assert build_service().is_available()
    assert not build_service(availability_24_7=False).is_available()