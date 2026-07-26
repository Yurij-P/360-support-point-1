from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
    SpatialTopographyFeature,
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
        topography_features=(SpatialTopographyFeature.RIVER_BASIN,),
    )

    res = service.evaluate_compatibility("scen_flooding_v1", passport)
    assert res.is_compatible is True
    assert res.match_score == 100.0
    assert len(res.missing_prerequisites) == 0


def test_scenario_topography_landslide_mountainous_verkhovyna_success() -> None:
    service = ScenarioCatalogService()

    pass_road = InfrastructureItemReadModel(
        id="infra_pass_1",
        name="Гірський перевал Р-24",
        category=CriticalInfrastructureCategory.MOUNTAIN_PASS_ROAD,
        latitude=48.15,
        longitude=24.83,
    )
    rockfall = InfrastructureItemReadModel(
        id="infra_rockfall_1",
        name="Зсувонебезпечний схил",
        category=CriticalInfrastructureCategory.LANDSLIDE_ROCKFALL_ZONE,
        latitude=48.16,
        longitude=24.84,
    )

    verkhovyna_passport = CommunityPassportReadModel(
        community_id="comm_verkhovyna_1",
        name="Верховинська селищна громада",
        official_code="UA26020010000049282",
        region="Івано-Франківська область",
        district="Верховинський район",
        area_sq_km=1050.0,
        total_population=18000,
        preparedness_score=65.0,
        maturity_level="Integrated",
        vulnerable_population_total=2500,
        infrastructure_items=(pass_road, rockfall),
        topography_features=(SpatialTopographyFeature.MOUNTAINOUS_TERRAIN,),
    )

    res = service.evaluate_compatibility("scen_landslide_v1", verkhovyna_passport)
    assert res.is_compatible is True
    assert res.match_score == 100.0
    assert len(res.missing_prerequisites) == 0


def test_scenario_topography_landslide_flat_shiroke_fails() -> None:
    service = ScenarioCatalogService()

    # Flat steppe community (Shiroke / Bereznehuvate)
    hospital = InfrastructureItemReadModel(
        id="infra_hosp_1",
        name="Лікарня",
        category=CriticalInfrastructureCategory.HOSPITAL_MEDICAL,
        latitude=47.3,
        longitude=32.8,
    )

    shiroke_passport = CommunityPassportReadModel(
        community_id="comm_shiroke_1",
        name="Широківська сільська громада",
        official_code="UA23080270000045612",
        region="Запорізька область",
        district="Запорізький район",
        area_sq_km=450.0,
        total_population=14000,
        preparedness_score=70.0,
        maturity_level="Integrated",
        vulnerable_population_total=2000,
        infrastructure_items=(hospital,),
        topography_features=(SpatialTopographyFeature.STEPPE_FLATLAND,),
    )

    res = service.evaluate_compatibility("scen_landslide_v1", shiroke_passport)
    assert res.is_compatible is False
    assert res.match_score < 100.0
    assert any("MOUNTAINOUS_TERRAIN" in err for err in res.missing_prerequisites)


def test_scenario_universal_military_threat_anywhere() -> None:
    service = ScenarioCatalogService()

    tro_hq = InfrastructureItemReadModel(
        id="infra_tro_1",
        name="Штаб ТрО",
        category=CriticalInfrastructureCategory.TERRITORIAL_DEFENSE_HQ,
        latitude=47.3,
        longitude=32.8,
    )
    checkpoint = InfrastructureItemReadModel(
        id="infra_chk_1",
        name="Блокпост",
        category=CriticalInfrastructureCategory.MILITARY_CHECKPOINT,
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
    hospital = InfrastructureItemReadModel(
        id="infra_hosp_1",
        name="Лікарня",
        category=CriticalInfrastructureCategory.HOSPITAL_MEDICAL,
        latitude=47.33,
        longitude=32.83,
    )

    passport = CommunityPassportReadModel(
        community_id="comm_anywhere_1",
        name="Довільна громада",
        official_code="UA999999",
        region="Будь-яка область",
        district="Будь-який район",
        area_sq_km=500.0,
        total_population=15000,
        preparedness_score=60.0,
        maturity_level="Integrated",
        vulnerable_population_total=1800,
        infrastructure_items=(tro_hq, checkpoint, bridge, hospital),
        topography_features=(SpatialTopographyFeature.STEPPE_FLATLAND,),
    )

    res = service.evaluate_compatibility("scen_wartime_defense_v1", passport)
    assert res.is_compatible is True
    assert res.match_score == 100.0
