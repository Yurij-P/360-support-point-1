from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation


@dataclass(frozen=True, kw_only=True)
class SimulationContext:
    """Immutable identifiers and versions that make a simulation run reproducible."""

    id: UUID
    community_id: UUID
    community_profile_id: UUID
    community_profile_version: str
    community_map_id: UUID
    community_map_version: int
    scenario_id: UUID
    scenario_version: int
    primary_threat_id: UUID
    secondary_threat_ids: tuple[UUID, ...] = ()
    available_resource_ids: tuple[UUID, ...] = ()
    operational_capability_ids: tuple[UUID, ...] = ()
    participating_organization_ids: tuple[UUID, ...] = ()
    participating_emergency_service_ids: tuple[UUID, ...] = ()
    affected_settlement_ids: tuple[UUID, ...] = ()
    initial_assumptions: tuple[str, ...] = ()
    data_quality_score: float
    created_at: datetime
    checksum: str

    def __post_init__(self) -> None:
        if not self.community_profile_version.strip():
            raise DomainRuleViolation("Community profile version must not be empty.")
        if self.community_map_version < 1:
            raise DomainRuleViolation("Community map version must be at least one.")
        if self.scenario_version < 1:
            raise DomainRuleViolation("Scenario version must be at least one.")
        if not 0 <= self.data_quality_score <= 100:
            raise DomainRuleViolation("Data quality score must be between zero and 100.")
        if self.primary_threat_id in self.secondary_threat_ids:
            raise DomainRuleViolation("Primary threat must not appear among secondary threats.")
        self._validate_unique_ids(self.secondary_threat_ids, "Secondary threat IDs")
        self._validate_unique_ids(self.available_resource_ids, "Available resource IDs")
        self._validate_unique_ids(self.operational_capability_ids, "Operational capability IDs")
        self._validate_unique_ids(self.participating_organization_ids, "Participating organization IDs")
        self._validate_unique_ids(
            self.participating_emergency_service_ids,
            "Participating emergency service IDs",
        )
        self._validate_unique_ids(self.affected_settlement_ids, "Affected settlement IDs")
        if any(not assumption.strip() for assumption in self.initial_assumptions):
            raise DomainRuleViolation("Initial assumptions must not contain empty strings.")
        if not self.checksum.strip():
            raise DomainRuleViolation("Context checksum must not be empty.")

    def all_threat_ids(self) -> tuple[UUID, ...]:
        return (self.primary_threat_id, *self.secondary_threat_ids)

    def includes_resource(self, resource_id: UUID) -> bool:
        return resource_id in self.available_resource_ids

    def includes_capability(self, capability_id: UUID) -> bool:
        return capability_id in self.operational_capability_ids

    def includes_organization(self, organization_id: UUID) -> bool:
        return organization_id in self.participating_organization_ids

    def affects_settlement(self, settlement_id: UUID) -> bool:
        return settlement_id in self.affected_settlement_ids

    def validate_for_start(self) -> None:
        if self.community_id is None:
            raise DomainRuleViolation("Simulation context requires a community ID.")
        if (
            self.community_profile_id is None
            or self.community_map_id is None
            or self.scenario_id is None
        ):
            raise DomainRuleViolation("Simulation context requires profile, map, and scenario IDs.")
        if self.data_quality_score < 60:
            raise DomainRuleViolation("Simulation context data quality score must be at least 60.")
        if not self.participating_organization_ids:
            raise DomainRuleViolation("Simulation context requires participating organizations.")
        if self.primary_threat_id is None:
            raise DomainRuleViolation("Simulation context requires a primary threat ID.")
        if not self.checksum.strip():
            raise DomainRuleViolation("Simulation context checksum must not be empty.")

    @staticmethod
    def _validate_unique_ids(ids: tuple[UUID, ...], label: str) -> None:
        if len(set(ids)) != len(ids):
            raise DomainRuleViolation(f"{label} must not contain duplicates.")