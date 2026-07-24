from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.geospatial.domain.enums import AccessLevel

from .enums import ResourceType, VerificationStatus


@dataclass
class ResourceInventoryItem:
    """An MVP inventory record for a community resource."""

    id: UUID
    name: str
    resource_type: ResourceType
    quantity: int
    unit: str
    owner_organization_id: UUID
    storage_geo_feature_id: UUID | None
    availability_status: str
    operational_status: str
    activation_time_minutes: int
    technical_specifications: dict[str, str | int | float | bool]
    required_operator_capabilities: tuple[str, ...]
    compatible_facility_ids: tuple[UUID, ...]
    consumables: dict[str, float]
    autonomy_hours: float | None
    limitations: tuple[str, ...]
    access_level: AccessLevel
    verification_status: VerificationStatus
    last_verified_at: datetime | None
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.unit.strip():
            raise ProfileRuleViolation("Resource name and unit must not be empty.")
        if self.quantity < 0:
            raise ProfileRuleViolation("Quantity must not be negative.")
        if self.activation_time_minutes < 0:
            raise ProfileRuleViolation("Activation time must not be negative.")
        if self.autonomy_hours is not None and self.autonomy_hours < 0:
            raise ProfileRuleViolation("Autonomy hours must not be negative.")
        if any(not key.strip() for key in self.technical_specifications):
            raise ProfileRuleViolation("Technical specification keys must not be empty.")
        if any(not capability.strip() for capability in self.required_operator_capabilities):
            raise ProfileRuleViolation("Operator capabilities must not contain empty strings.")
        if len(set(self.compatible_facility_ids)) != len(self.compatible_facility_ids):
            raise ProfileRuleViolation("Compatible facility IDs must not contain duplicates.")
        if any(not key.strip() or value < 0 for key, value in self.consumables.items()):
            raise ProfileRuleViolation("Consumables require non-empty names and non-negative values.")
        if any(not limitation.strip() for limitation in self.limitations):
            raise ProfileRuleViolation("Limitations must not contain empty strings.")
        if any(not item.strip() for item in self.evidence):
            raise ProfileRuleViolation("Evidence must not contain empty strings.")

    def is_available(self) -> bool:
        return (
            self.availability_status.strip().lower() == "available"
            and self.operational_status.strip().lower() == "operational"
        )

    def requires_operator(self) -> bool:
        return bool(self.required_operator_capabilities)

    def supports_facility(self, facility_id: UUID) -> bool:
        return facility_id in self.compatible_facility_ids

    def estimated_operational_hours(self, available_consumables: dict[str, float]) -> float | None:
        """Return an MVP consumable-based estimate; this is not an energy calculator."""
        if self.autonomy_hours is not None and not self.consumables:
            return self.autonomy_hours

        consumption_per_hour = self.technical_specifications.get("consumption_per_hour")
        if (
            not isinstance(consumption_per_hour, int | float)
            or isinstance(consumption_per_hour, bool)
            or consumption_per_hour <= 0
        ):
            return None

        matching_amounts = [
            amount
            for name, amount in available_consumables.items()
            if name in self.consumables and amount >= 0
        ]
        if not matching_amounts:
            return None
        return min(matching_amounts) / consumption_per_hour