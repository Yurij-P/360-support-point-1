from dataclasses import dataclass, field
from uuid import UUID, uuid4

from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.community_profile.value_objects import PopulationCount

from .enums import VerificationStatus


@dataclass
class Settlement:
    """A settlement within a community profile."""

    name: str
    settlement_type: str
    population: PopulationCount
    id: UUID = field(default_factory=uuid4, init=False)
    starosta_district: str | None = None
    geo_feature_id: UUID | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ProfileRuleViolation("Settlement name must not be empty.")
        if not self.settlement_type.strip():
            raise ProfileRuleViolation("Settlement type must not be empty.")
        if any(not item.strip() for item in self.evidence):
            raise ProfileRuleViolation("Settlement evidence must not contain empty strings.")
