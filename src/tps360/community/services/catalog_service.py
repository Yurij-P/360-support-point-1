from __future__ import annotations

from dataclasses import dataclass

from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
)
from tps360.community.domain.passport_read_model import (
    CommunityPassportReadModel,
    InfrastructureItemReadModel,
)
from tps360.core.exceptions import EntityNotFound


@dataclass(frozen=True)
class CommunityCatalogItem:
    community_id: str
    name: str
    official_code: str
    region: str
    district: str
    total_population: int
    preparedness_score: float
    maturity_level: str
    critical_infrastructure_count: int


# Default catalog dataset (Bereznehuvate, Mykolaiv, Kherson, Odesa demo seeds)
SEED_PASSPORTS: dict[str, CommunityPassportReadModel] = {
    "a29d6fbd-02c3-4d43-a651-7efd6fbd02c3": CommunityPassportReadModel(
        community_id="a29d6fbd-02c3-4d43-a651-7efd6fbd02c3",
        name="Березнегуватська селищна громада",
        official_code="UA48060030000037887",
        region="Миколаївська область",
        district="Баштанський район",
        area_sq_km=872.4,
        total_population=23500,
        preparedness_score=68.5,
        maturity_level="Integrated",
        vulnerable_population_total=4200,
        vulnerable_groups_breakdown={
            "children": 1800,
            "elderly": 1500,
            "disabled": 450,
            "idp": 450,
        },
        osm_relation_id="osm_rel_bereznehuvate_1784",
        bounding_box={"min_lat": 47.1, "min_lon": 32.7, "max_lat": 47.6, "max_lon": 33.3},
        infrastructure_items=(
            InfrastructureItemReadModel(
                id="infra_berez_poultry_1",
                name="Березнегуватська птахофабрика",
                category=CriticalInfrastructureCategory.POULTRY_FARM,
                latitude=47.31,
                longitude=32.85,
                risk_level="HIGH",
            ),
            InfrastructureItemReadModel(
                id="infra_berez_substation_1",
                name="Баштанська ТП 110кВ",
                category=CriticalInfrastructureCategory.TRANSFORMER_SUBSTATION,
                latitude=47.33,
                longitude=32.88,
                risk_level="CRITICAL",
            ),
            InfrastructureItemReadModel(
                id="infra_berez_pipeline_1",
                name="Березнегуватська ГРС та газопровід",
                category=CriticalInfrastructureCategory.GAS_PIPELINE,
                latitude=47.30,
                longitude=32.82,
                risk_level="HIGH",
            ),
            InfrastructureItemReadModel(
                id="infra_berez_bridge_1",
                name="Міст через р. Висунь",
                category=CriticalInfrastructureCategory.BRIDGE_VIADUCT,
                latitude=47.32,
                longitude=32.86,
                risk_level="HIGH",
            ),
            InfrastructureItemReadModel(
                id="infra_berez_hospital_1",
                name="Березнегуватська центральна лікарня",
                category=CriticalInfrastructureCategory.HOSPITAL_MEDICAL,
                latitude=47.315,
                longitude=32.845,
                risk_level="MODERATE",
            ),
        ),
    ),
}


class CommunityCatalogService:
    """Service providing search, filtering, and passport read model access for communities."""

    def __init__(self, passports: dict[str, CommunityPassportReadModel] | None = None) -> None:
        self._passports = passports if passports is not None else SEED_PASSPORTS

    def search_catalog(
        self,
        query: str | None = None,
        region: str | None = None,
        min_preparedness: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CommunityCatalogItem]:
        items: list[CommunityCatalogItem] = []

        for p in self._passports.values():
            if query and query.lower() not in p.name.lower() and query.lower() not in p.official_code.lower():
                continue
            if region and region.lower() not in p.region.lower():
                continue
            if min_preparedness is not None and p.preparedness_score < min_preparedness:
                continue

            items.append(
                CommunityCatalogItem(
                    community_id=p.community_id,
                    name=p.name,
                    official_code=p.official_code,
                    region=p.region,
                    district=p.district,
                    total_population=p.total_population,
                    preparedness_score=p.preparedness_score,
                    maturity_level=p.maturity_level,
                    critical_infrastructure_count=p.critical_infrastructure_count,
                )
            )

        return items[offset : offset + limit]

    def get_passport(self, community_id: str) -> CommunityPassportReadModel:
        if community_id not in self._passports:
            raise EntityNotFound(f"Community passport with id '{community_id}' not found.")
        return self._passports[community_id]
