from __future__ import annotations

from dataclasses import dataclass

from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
    SpatialTopographyFeature,
)
from tps360.community.domain.passport_read_model import CommunityPassportReadModel
from tps360.core.exceptions import EntityNotFound
from tps360.simulation.domain.time_dilation import CrisisVelocity


@dataclass(frozen=True)
class ScenarioCompatibilityResult:
    scenario_id: str
    community_id: str
    is_compatible: bool
    match_score: float  # 0.0 to 100.0
    required_categories: tuple[CriticalInfrastructureCategory, ...]
    found_categories: tuple[CriticalInfrastructureCategory, ...]
    required_topography: tuple[SpatialTopographyFeature, ...]
    missing_prerequisites: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioTemplateCatalogItem:
    id: str
    title: str
    description: str
    difficulty: str
    threat_category: str
    crisis_velocity: CrisisVelocity
    target_round_duration: int
    required_infrastructure: tuple[CriticalInfrastructureCategory, ...]
    required_topography: tuple[SpatialTopographyFeature, ...] = ()


# Dynamic catalog templates. Note: Topographical and infrastructure requirements are non-dogmatic.
# They serve as open spatial criteria evaluated against dynamic OpenStreetMap/GIS layers of any target community.
SEED_SCENARIOS: dict[str, ScenarioTemplateCatalogItem] = {
    "scen_flooding_v1": ScenarioTemplateCatalogItem(
        id="scen_flooding_v1",
        title="Весняна повінь та руйнування гідроспоруд",
        description="Комплексна кризова симуляція поводі, підтоплення житлових масивів та загрози греблям.",
        difficulty="MODERATE",
        threat_category="NATURAL",
        crisis_velocity=CrisisVelocity.FAST,
        target_round_duration=15,
        required_infrastructure=(
            CriticalInfrastructureCategory.RIVER_WATERWAY,
            CriticalInfrastructureCategory.DAM_HYDRO_STRUCTURE,
            CriticalInfrastructureCategory.BRIDGE_VIADUCT,
        ),
        required_topography=(SpatialTopographyFeature.RIVER_BASIN,),
    ),
    "scen_landslide_v1": ScenarioTemplateCatalogItem(
        id="scen_landslide_v1",
        title="Зсув ґрунту та каменепад на автодорогу",
        description="НС геоморфологічного типу: блокування автошляхів та перекриття транспортних артерій у схилових/гірських зонах.",
        difficulty="HIGH",
        threat_category="NATURAL",
        crisis_velocity=CrisisVelocity.FAST,
        target_round_duration=20,
        required_infrastructure=(
            CriticalInfrastructureCategory.MOUNTAIN_PASS_ROAD,
            CriticalInfrastructureCategory.LANDSLIDE_ROCKFALL_ZONE,
        ),
        required_topography=(SpatialTopographyFeature.MOUNTAINOUS_TERRAIN,),
    ),
    "scen_nuclear_fallout_v1": ScenarioTemplateCatalogItem(
        id="scen_nuclear_fallout_v1",
        title="Радіаційна загроза та аварія на АЕС",
        description="Симуляція радіаційного забруднення у зоні спостереження атомної електростанції.",
        difficulty="CRITICAL",
        threat_category="TECHNOGENIC",
        crisis_velocity=CrisisVelocity.SLOW_MAX,
        target_round_duration=30,
        required_infrastructure=(
            CriticalInfrastructureCategory.NUCLEAR_PROXIMITY_ZONE,
            CriticalInfrastructureCategory.HOSPITAL_MEDICAL,
        ),
        required_topography=(SpatialTopographyFeature.NUCLEAR_PROXIMITY,),
    ),
    "scen_epizootic_v1": ScenarioTemplateCatalogItem(
        id="scen_epizootic_v1",
        title="Спалах африканської чуми свиней та епізоотія",
        description="Кризова біозагроза у сільському господарстві з викликом санітарного карантину.",
        difficulty="HIGH",
        threat_category="BIOLOGICAL",
        crisis_velocity=CrisisVelocity.SLOW_MAX,
        target_round_duration=20,
        required_infrastructure=(
            CriticalInfrastructureCategory.LIVESTOCK_COMPLEX,
            CriticalInfrastructureCategory.POULTRY_FARM,
            CriticalInfrastructureCategory.EPIZOOTIC_BURIAL_SITE,
        ),
    ),
    "scen_blackout_v1": ScenarioTemplateCatalogItem(
        id="scen_blackout_v1",
        title="Системна аварія енергомережі та блек-аут",
        description="Повне знеструмлення критичної інфраструктури громади та котелень у зимовий період.",
        difficulty="CRITICAL",
        threat_category="TECHNOGENIC",
        crisis_velocity=CrisisVelocity.SLOW_MAX,
        target_round_duration=30,
        required_infrastructure=(
            CriticalInfrastructureCategory.TRANSFORMER_SUBSTATION,
            CriticalInfrastructureCategory.POWER_LINE,
            CriticalInfrastructureCategory.BOILER_PLANT,
            CriticalInfrastructureCategory.HOSPITAL_MEDICAL,
        ),
    ),
    "scen_wartime_defense_v1": ScenarioTemplateCatalogItem(
        id="scen_wartime_defense_v1",
        title="Воєнний стан, ракетно-дронові удари та логістичний колапс",
        description="Універсальна воєнна криза: ракетні удари, атаки БПЛА по будь-якій території громади.",
        difficulty="CRITICAL",
        threat_category="MILITARY",
        crisis_velocity=CrisisVelocity.FAST,
        target_round_duration=30,
        required_infrastructure=(
            CriticalInfrastructureCategory.TERRITORIAL_DEFENSE_HQ,
            CriticalInfrastructureCategory.MILITARY_CHECKPOINT,
            CriticalInfrastructureCategory.BRIDGE_VIADUCT,
            CriticalInfrastructureCategory.HOSPITAL_MEDICAL,
        ),
        required_topography=(SpatialTopographyFeature.UNIVERSAL_WIDESPREAD,),
    ),
}


class ScenarioCatalogService:
    """Generic open service managing simulation scenario discovery and map-based compatibility evaluation for ANY community."""

    def __init__(self, scenarios: dict[str, ScenarioTemplateCatalogItem] | None = None) -> None:
        self._scenarios = scenarios if scenarios is not None else SEED_SCENARIOS

    def list_scenarios(self, threat_category: str | None = None) -> list[ScenarioTemplateCatalogItem]:
        if not threat_category:
            return list(self._scenarios.values())
        return [s for s in self._scenarios.values() if s.threat_category.upper() == threat_category.upper()]

    def get_scenario(self, scenario_id: str) -> ScenarioTemplateCatalogItem:
        if scenario_id not in self._scenarios:
            raise EntityNotFound(f"Scenario template with id '{scenario_id}' not found.")
        return self._scenarios[scenario_id]

    def evaluate_compatibility(
        self, scenario_id: str, passport: CommunityPassportReadModel
    ) -> ScenarioCompatibilityResult:
        """Dynamically evaluates map & spatial compatibility of a scenario against a community's passport.
        
        Important Domain Rule: Spatial features and infrastructure requirements are NOT dogmatic or tied to specific community names.
        They represent dynamic GIS criteria matched against whatever OpenStreetMap/spatial layers exist in the provided passport.
        """
        scenario = self.get_scenario(scenario_id)

        present_categories = set(item.category for item in passport.infrastructure_items)
        required_infra = set(scenario.required_infrastructure)

        found_infra = present_categories.intersection(required_infra)
        missing_infra = required_infra - found_infra

        # Dynamic spatial topography validation
        present_topography = set(passport.topography_features)
        required_topo = set(scenario.required_topography)

        missing_prereqs: list[str] = []
        warnings: list[str] = []

        # Universal threats (e.g. Missiles/UAVs) can occur anywhere on the map
        is_universal_threat = (
            SpatialTopographyFeature.UNIVERSAL_WIDESPREAD in required_topo
            or not required_topo
        )

        topography_match = True
        if not is_universal_threat:
            for req_t in required_topo:
                if req_t not in present_topography:
                    topography_match = False
                    missing_prereqs.append(
                        f"Неможливо за картографічними даними: даний сценарій вимагає геопросторової риси {req_t.value}, яка відсутня у топографічному шарі даної громади."
                    )

        if missing_infra:
            for m in missing_infra:
                missing_prereqs.append(f"Відсутній обов'язковий об'єкт інфраструктури: {m.value}")

        total_requirements_count = len(required_infra) + (0 if is_universal_threat else len(required_topo))
        met_requirements_count = len(found_infra) + (0 if is_universal_threat else len(required_topo.intersection(present_topography)))

        match_score = (met_requirements_count / total_requirements_count * 100.0) if total_requirements_count > 0 else 100.0

        # Check preparedness score warning
        if passport.preparedness_score < 50.0:
            warnings.append("Низький бал готовності громади (< 50.0) підвищує ризик негативних наслідків.")

        is_compatible = (len(missing_infra) == 0) and topography_match

        return ScenarioCompatibilityResult(
            scenario_id=scenario.id,
            community_id=passport.community_id,
            is_compatible=is_compatible,
            match_score=round(match_score, 1),
            required_categories=tuple(scenario.required_infrastructure),
            found_categories=tuple(found_infra),
            required_topography=tuple(scenario.required_topography),
            missing_prerequisites=tuple(missing_prereqs),
            warnings=tuple(warnings),
        )
