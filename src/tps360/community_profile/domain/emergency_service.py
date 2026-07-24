from dataclasses import dataclass
from uuid import UUID

from tps360.community_profile.exceptions import ProfileRuleViolation

from .enums import OrganizationType, VerificationStatus


@dataclass
class EmergencyService:
    """An emergency service operated by a community organization."""

    id: UUID
    organization_id: UUID
    service_type: OrganizationType
    operational_status: str
    availability_24_7: bool
    response_time_minutes: int
    personnel_count: int
    vehicle_count: int
    service_area: tuple[UUID, ...]
    geo_feature_id: UUID | None
    capabilities: tuple[str, ...]
    verification_status: VerificationStatus
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.response_time_minutes < 0:
            raise ProfileRuleViolation("Response time must not be negative.")
        if self.personnel_count < 0:
            raise ProfileRuleViolation("Personnel count must not be negative.")
        if self.vehicle_count < 0:
            raise ProfileRuleViolation("Vehicle count must not be negative.")
        if len(set(self.service_area)) != len(self.service_area):
            raise ProfileRuleViolation("Service area must not contain duplicates.")
        if any(not capability.strip() for capability in self.capabilities):
            raise ProfileRuleViolation("Capabilities must not contain empty strings.")
        if any(not item.strip() for item in self.evidence):
            raise ProfileRuleViolation("Evidence must not contain empty strings.")

    def serves(self, settlement_id: UUID) -> bool:
        return settlement_id in self.service_area

    def is_available(self) -> bool:
        return self.availability_24_7 and self.operational_status.strip().lower() == "operational"