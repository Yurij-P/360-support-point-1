from dataclasses import dataclass
from uuid import UUID

from tps360.community_profile.domain.enums import FacilityType, OrganizationType, ResourceType
from tps360.community_profile.domain.organization import Organization
from tps360.community_profile.domain.resource_inventory import ResourceInventoryItem
from tps360.community_profile.exceptions import ProfileRuleViolation


@dataclass
class OperationalCapability:
    """A community capability assessed against its available operational inputs."""

    id: UUID
    name: str
    required_resource_types: tuple[ResourceType, ...]
    required_facility_types: tuple[FacilityType, ...]
    required_organization_types: tuple[OrganizationType, ...]
    required_people: int
    activation_time_minutes: int
    operational_duration_hours: float
    priority: int
    is_available: bool

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ProfileRuleViolation("Operational capability name must not be empty.")
        if self.required_people < 0:
            raise ProfileRuleViolation("Required people must not be negative.")
        if self.activation_time_minutes < 0:
            raise ProfileRuleViolation("Activation time must not be negative.")
        if self.operational_duration_hours < 0:
            raise ProfileRuleViolation("Operational duration must not be negative.")
        if self.priority < 0:
            raise ProfileRuleViolation("Priority must not be negative.")

    def calculate_availability(
        self,
        resources: tuple[ResourceInventoryItem, ...],
        available_facility_types: tuple[FacilityType, ...],
        organizations: tuple[Organization, ...],
        available_people: int,
    ) -> bool:
        self.is_available = self.can_execute(
            resources,
            available_facility_types,
            organizations,
            available_people,
        )
        return self.is_available

    def calculate_missing_resources(
        self, resources: tuple[ResourceInventoryItem, ...]
    ) -> tuple[ResourceType, ...]:
        available_resource_types = {
            resource.resource_type
            for resource in resources
            if resource.quantity > 0 and resource.is_available()
        }
        return tuple(
            resource_type
            for resource_type in self.required_resource_types
            if resource_type not in available_resource_types
        )

    def calculate_missing_people(self, available_people: int) -> int:
        if available_people < 0:
            raise ProfileRuleViolation("Available people must not be negative.")
        return max(self.required_people - available_people, 0)

    def can_execute(
        self,
        resources: tuple[ResourceInventoryItem, ...],
        available_facility_types: tuple[FacilityType, ...],
        organizations: tuple[Organization, ...],
        available_people: int,
    ) -> bool:
        available_organization_types = {
            organization.organization_type for organization in organizations
        }
        return (
            not self.calculate_missing_resources(resources)
            and set(self.required_facility_types).issubset(available_facility_types)
            and set(self.required_organization_types).issubset(available_organization_types)
            and self.calculate_missing_people(available_people) == 0
        )