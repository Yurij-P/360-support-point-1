from __future__ import annotations

from dataclasses import dataclass, field

from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
    get_osm_tag_mapping,
)
from tps360.core.exceptions import DomainRuleViolation


@dataclass(frozen=True)
class InfrastructureItemReadModel:
    id: str
    name: str
    category: CriticalInfrastructureCategory
    latitude: float
    longitude: float
    risk_level: str = "MODERATE"
    osm_key: str = ""
    osm_value: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.name:
            raise DomainRuleViolation("Infrastructure item requires id and name.")
        if not (-90.0 <= self.latitude <= 90.0) or not (-180.0 <= self.longitude <= 180.0):
            raise DomainRuleViolation("Invalid latitude or longitude coordinates.")

        if not self.osm_key or not self.osm_value:
            mapping = get_osm_tag_mapping(self.category)
            object.__setattr__(self, "osm_key", mapping.osm_key)
            object.__setattr__(self, "osm_value", mapping.osm_value)


@dataclass(frozen=True)
class CommunityPassportReadModel:
    """Immutable aggregate read-model for a community passport including OpenStreetMap critical infrastructure."""

    community_id: str
    name: str
    official_code: str  # KATOTTG or KOATUU code
    region: str
    district: str
    area_sq_km: float
    total_population: int
    preparedness_score: float
    maturity_level: str
    vulnerable_population_total: int
    vulnerable_groups_breakdown: dict[str, int] = field(default_factory=dict)
    infrastructure_items: tuple[InfrastructureItemReadModel, ...] = ()
    osm_relation_id: str | None = None
    bounding_box: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if not self.community_id or not self.name or not self.official_code:
            raise DomainRuleViolation("Community Passport requires community_id, name, and official_code.")
        if self.area_sq_km <= 0 or self.total_population < 0:
            raise DomainRuleViolation("Area must be positive and population non-negative.")

    @property
    def critical_infrastructure_count(self) -> int:
        return len(self.infrastructure_items)

    def get_items_by_category(
        self, category: CriticalInfrastructureCategory
    ) -> list[InfrastructureItemReadModel]:
        return [item for item in self.infrastructure_items if item.category == category]
