from __future__ import annotations

from dataclasses import dataclass

from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
)
from tps360.community.domain.katottg_directory import OFFICIAL_KATOTTG_DATASET
from tps360.community.domain.passport_read_model import (
    CommunityPassportReadModel,
    InfrastructureItemReadModel,
)
from tps360.core.exceptions import EntityNotFound


@dataclass(frozen=True)
class CommunityCatalogItem:
    community_id: str
    name: str
    official_code: str  # KATOTTG code (e.g., UA48060030000037887)
    region: str
    district: str
    total_population: int
    preparedness_score: float
    maturity_level: str
    critical_infrastructure_count: int
    center_latitude: float = 48.155
    center_longitude: float = 24.832


def _build_initial_passports() -> dict[str, CommunityPassportReadModel]:
    passports: dict[str, CommunityPassportReadModel] = {}

    for record in OFFICIAL_KATOTTG_DATASET:
        comm_id = record.official_code.lower()

        passports[comm_id] = CommunityPassportReadModel(
            community_id=comm_id,
            name=record.name,
            official_code=record.official_code,
            region=record.region,
            district=record.district,
            area_sq_km=450.0,
            total_population=record.total_population,
            preparedness_score=72.0,
            maturity_level="Integrated",
            vulnerable_population_total=int(record.total_population * 0.18),
            center_latitude=record.center_latitude,
            center_longitude=record.center_longitude,
            vulnerable_groups_breakdown={
                "children": int(record.total_population * 0.08),
                "elderly": int(record.total_population * 0.07),
                "disabled": int(record.total_population * 0.02),
                "idp": int(record.total_population * 0.01),
            },
            infrastructure_items=(
                InfrastructureItemReadModel(
                    id=f"infra_{record.official_code}_hq",
                    name=f"Штаб НС ({record.name})",
                    category=CriticalInfrastructureCategory.TERRITORIAL_DEFENSE_HQ,
                    latitude=record.center_latitude,
                    longitude=record.center_longitude,
                    risk_level="LOW",
                ),
                InfrastructureItemReadModel(
                    id=f"infra_{record.official_code}_fire",
                    name=f"Пожежно-рятувальна частина ДСНС ({record.name})",
                    category=CriticalInfrastructureCategory.RESCUE_FIRE_STATION,
                    latitude=record.center_latitude + 0.004,
                    longitude=record.center_longitude + 0.005,
                    risk_level="LOW",
                ),
                InfrastructureItemReadModel(
                    id=f"infra_{record.official_code}_hosp",
                    name=f"Центральна міська лікарня ({record.name})",
                    category=CriticalInfrastructureCategory.HOSPITAL_MEDICAL,
                    latitude=record.center_latitude - 0.003,
                    longitude=record.center_longitude - 0.004,
                    risk_level="MODERATE",
                ),
                InfrastructureItemReadModel(
                    id=f"infra_{record.official_code}_sub",
                    name="Трансформаторна підстанція 110кВ",
                    category=CriticalInfrastructureCategory.TRANSFORMER_SUBSTATION,
                    latitude=record.center_latitude + 0.012,
                    longitude=record.center_longitude + 0.015,
                    risk_level="HIGH",
                ),
            ),
        )

    return passports


class CommunityCatalogService:
    """Service providing search, filtering, and passport read model access for communities."""

    def __init__(self, passports: dict[str, CommunityPassportReadModel] | None = None) -> None:
        self._passports = passports if passports is not None else _build_initial_passports()

    def search_catalog(
        self,
        query: str | None = None,
        region: str | None = None,
        min_preparedness: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CommunityCatalogItem]:
        items: list[CommunityCatalogItem] = []
        q_clean = query.strip().lower() if query else ""

        # If query is a custom KATOTTG code (starts with UA or digits) not yet in dictionary, dynamically register it
        if q_clean and (q_clean.startswith("ua") or q_clean.isdigit()) and len(q_clean) >= 5:
            code_upper = q_clean.upper()
            if not any(code_upper in p.official_code for p in self._passports.values()):
                dynamic_id = code_upper.lower()
                self._passports[dynamic_id] = CommunityPassportReadModel(
                    community_id=dynamic_id,
                    name=f"Територіальна громада ({code_upper})",
                    official_code=code_upper,
                    region="Україна (КАТОТТГ)",
                    district="Район КАТОТТГ",
                    area_sq_km=500.0,
                    total_population=21000,
                    preparedness_score=70.0,
                    maturity_level="Integrated",
                    vulnerable_population_total=3500,
                    center_latitude=49.0,
                    center_longitude=31.0,
                    infrastructure_items=(
                        InfrastructureItemReadModel(
                            id=f"infra_{code_upper}_1",
                            name=f"Штаб НС ({code_upper})",
                            category=CriticalInfrastructureCategory.TERRITORIAL_DEFENSE_HQ,
                            latitude=49.0,
                            longitude=31.0,
                            risk_level="MODERATE",
                        ),
                    ),
                )

        # Sort passports systematically: Kyiv City first, then by Region, then by Name
        sorted_passports = sorted(
            self._passports.values(),
            key=lambda p: (0 if "Київ" in p.region else 1, p.region, p.name)
        )

        for p in sorted_passports:
            if q_clean:
                name_match = q_clean in p.name.lower()
                code_match = q_clean in p.official_code.lower()
                region_match = q_clean in p.region.lower()
                district_match = q_clean in p.district.lower()
                if not (name_match or code_match or region_match or district_match):
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
                    center_latitude=p.center_latitude,
                    center_longitude=p.center_longitude,
                )
            )

        return items[offset : offset + limit]

    def get_passport(self, community_id: str) -> CommunityPassportReadModel:
        cid_lower = community_id.lower()
        if cid_lower in self._passports:
            return self._passports[cid_lower]

        # Support lookups by KATOTTG official code or community id
        for p in self._passports.values():
            if p.official_code.lower() == cid_lower or p.community_id.lower() == cid_lower:
                return p

        raise EntityNotFound(f"Community passport with id '{community_id}' not found.")
