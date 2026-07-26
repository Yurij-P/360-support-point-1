from __future__ import annotations

from dataclasses import dataclass

from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
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


# Default Scenario Templates (Flooding, Epizootic, Blackout, Wartime Multi-Hazard)
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
        title="Воєнний стан, артилерійські обстріли та логістичний колапс",
        description="Потрійна криза: ураження енергетики, обстріли транспортних вузлів та евакуація населення.",
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
    ),
}


class ScenarioCatalogService:
    """Service managing simulation scenario discovery and community passport compatibility evaluation."""

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
        scenario = self.get_scenario(scenario_id)

        present_categories = set(item.category for item in passport.infrastructure_items)
        required = set(scenario.required_infrastructure)

        found = present_categories.intersection(required)
        missing = required - found

        match_score = (len(found) / len(required) * 100.0) if required else 100.0

        missing_prereqs: list[str] = []
        warnings: list[str] = []

        if missing:
            for m in missing:
                missing_prereqs.append(f"Відсутній обов'язковий об'єкт інфраструктури: {m.value}")

        # Check preparedness score warning
        if passport.preparedness_score < 50.0:
            warnings.append("Низький бал готовності громади (< 50.0) підвищує ризик негативних наслідків.")

        is_compatible = len(missing) == 0

        return ScenarioCompatibilityResult(
            scenario_id=scenario.id,
            community_id=passport.community_id,
            is_compatible=is_compatible,
            match_score=round(match_score, 1),
            required_categories=tuple(scenario.required_infrastructure),
            found_categories=tuple(found),
            missing_prerequisites=tuple(missing_prereqs),
            warnings=tuple(warnings),
        )
