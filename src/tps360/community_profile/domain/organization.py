from dataclasses import dataclass
from uuid import UUID

from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.community_profile.value_objects import ContactReference

from .enums import OrganizationType, VerificationStatus


@dataclass
class Organization:
    """An organization that provides services within a community."""

    id: UUID
    name: str
    organization_type: OrganizationType
    status: VerificationStatus
    contact_reference: ContactReference | None
    service_area: tuple[UUID, ...]
    geo_feature_id: UUID | None
    capabilities: tuple[str, ...]
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ProfileRuleViolation("Organization name must not be empty.")
        if len(set(self.service_area)) != len(self.service_area):
            raise ProfileRuleViolation("Service area must not contain duplicates.")
        if any(not capability.strip() for capability in self.capabilities):
            raise ProfileRuleViolation("Capabilities must not contain empty strings.")
        if any(not item.strip() for item in self.evidence):
            raise ProfileRuleViolation("Evidence must not contain empty strings.")

    def serves(self, settlement_id: UUID) -> bool:
        return settlement_id in self.service_area

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities