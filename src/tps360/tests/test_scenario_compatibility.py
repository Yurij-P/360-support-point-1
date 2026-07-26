from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
)
from tps360.community.domain.passport_read_model import (
    CommunityPassportReadModel,
    InfrastructureItemReadModel,
)
from tps360.simulation.services.scenario_catalog_service import (
    ScenarioCatalogService,
)


def test_scenario_compatibility_success() -> None:
    service = ScenarioCatalogService()

    # Community with River, Dam, Bridge
    river = InfrastructureItemReadModel(
        id="infra_river_1",
        name="р. Висунь",
        category=CriticalInfrastructureCategory.RIVER_WATERWAY,
        latitude=47.3,
        longitude=32.8,
    )
    dam = InfrastructureItemReadModel(
        id="infra_dam_1",
        name="Дамба Березнегувате",
        category=CriticalInfrastructureCategory.DAM_HYDRO_STRUCTURE,
        latitude=47.31,
        longitude=32.81,
    )
    bridge = InfrastructureItemReadModel(
        id="infra_bridge_1",
        name="Міст",
        category=CriticalInfrastructureCategory.BRIDGE_VIADUCT,
        latitude=47.32,
        longitude=32.82,
    )

    passport = CommunityPassportReadModel(
        community_id="comm_water_1",
        name="Громада біля річки",
        official_code="UA123456",
        region="Миколаївська область",
        district="Баштанський район",
        area_sq_km=300.0,
        total_population=10000,
        preparedness_score=75.0,
        maturity_level="Integrated",
        vulnerable_population_total=1500,
        infrastructure_items=(river, dam, bridge),
    )

    res = service.evaluate_compatibility("scen_flooding_v1", passport)
    assert res.is_compatible is True
    assert res.match_score == 100.0
    assert len(res.missing_prerequisites) == 0


def test_scenario_compatibility_missing_infrastructure() -> None:
    service = ScenarioCatalogService()

    # Community without Dam or River
    hospital = InfrastructureItemReadModel(
        id="infra_hosp_1",
        name="Лікарня",
        category=CriticalInfrastructureCategory.HOSPITAL_MEDICAL,
        latitude=47.3,
        longitude=32.8,
    )

    passport = CommunityPassportReadModel(
        community_id="comm_dry_1",
        name="Суха громада",
        official_code="UA654321",
        region="Миколаївська область",
        district="Баштанський район",
        area_sq_km=200.0,
        total_population=5000,
        preparedness_score=45.0,
        maturity_level="Basic",
        vulnerable_population_total=800,
        infrastructure_items=(hospital,),
    )

    res = service.evaluate_compatibility("scen_flooding_v1", passport)
    assert res.is_compatible is False
    assert res.match_score < 100.0
    assert len(res.missing_prerequisites) > 0
    assert len(res.warnings) > 0  # Low preparedness warning (< 50.0)
