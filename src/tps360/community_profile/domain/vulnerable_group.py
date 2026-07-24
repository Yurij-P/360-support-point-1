from dataclasses import dataclass
from uuid import UUID

from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.community_profile.value_objects import PopulationCount

from .enums import VerificationStatus


@dataclass
class VulnerableGroup:
    """A verified population group with shared support needs."""

    id: UUID
    name: str
    category: str
    estimated_count: PopulationCount
    geographic_scope: tuple[UUID, ...]
    support_needs: tuple[str, ...]
    responsible_organization_ids: tuple[UUID, ...]
    verification_status: VerificationStatus
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ProfileRuleViolation("Vulnerable group name must not be empty.")
        if not self.category.strip():
            raise ProfileRuleViolation("Vulnerable group category must not be empty.")
        if any(not need.strip() for need in self.support_needs):
            raise ProfileRuleViolation("Support needs must not contain empty strings.")
        if any(not item.strip() for item in self.evidence):
            raise ProfileRuleViolation("Evidence must not contain empty strings.")
        if len(set(self.geographic_scope)) != len(self.geographic_scope):
            raise ProfileRuleViolation("Geographic scope must not contain duplicates.")
        if len(set(self.responsible_organization_ids)) != len(self.responsible_organization_ids):
            raise ProfileRuleViolation("Responsible organizations must not contain duplicates.")

    def contains_settlement(self, settlement_id: UUID) -> bool:
        return settlement_id in self.geographic_scope