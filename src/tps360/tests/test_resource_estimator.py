from decimal import Decimal

from tps360.community.domain.infrastructure_taxonomy import CriticalInfrastructureCategory
from tps360.community.domain.passport_read_model import (
    CommunityPassportReadModel,
    InfrastructureItemReadModel,
)
from tps360.simulation.services.resource_estimator import estimate_role_resources


def _passport(population: int, area: float = 120.0, agri: int = 0) -> CommunityPassportReadModel:
    items = tuple(
        InfrastructureItemReadModel(
            id=f"farm_{i}",
            name=f"Птахоферма {i}",
            category=CriticalInfrastructureCategory.POULTRY_FARM,
            latitude=48.0,
            longitude=31.0,
        )
        for i in range(agri)
    )
    return CommunityPassportReadModel(
        community_id="ua00000000000000000",
        name="Тестова громада",
        official_code="UA00000000000000000",
        region="Область",
        district="Район",
        area_sq_km=area,
        total_population=population,
        preparedness_score=70.0,
        maturity_level="Integrated",
        vulnerable_population_total=int(population * 0.18),
        infrastructure_items=items,
    )


def test_deterministic() -> None:
    p = _passport(15000)
    assert estimate_role_resources("communal-utility", p) == estimate_role_resources(
        "communal-utility", p
    )


def test_personnel_is_present_per_role() -> None:
    p = _passport(15000)
    assert estimate_role_resources("emerg-dsns", p)["rescue_personnel"] > 0
    assert estimate_role_resources("emerg-police", p)["police_officers"] > 0
    assert estimate_role_resources("emerg-ems", p)["medical_personnel"] > 0
    assert estimate_role_resources("communal-utility", p)["utility_workers"] > 0


def test_personnel_scales_with_population() -> None:
    small = estimate_role_resources("emerg-police", _passport(5000))["police_officers"]
    big = estimate_role_resources("emerg-police", _passport(50000))["police_officers"]
    assert big > small


def test_utility_has_realistic_assets() -> None:
    res = estimate_role_resources("communal-utility", _passport(15000, area=200.0, agri=3))
    for key in ("tractors", "sewage_trucks", "utility_vehicles", "fuel_liters"):
        assert key in res
    # more agri objects and larger area -> more tractors
    fewer = estimate_role_resources("communal-utility", _passport(15000, area=40.0, agri=0))
    assert res["tractors"] > fewer["tractors"]


def test_unknown_role_uses_generic_fallback() -> None:
    res = estimate_role_resources("civil-ngo", _passport(15000))
    assert res["personnel"] > 0
    assert res["vehicles"] >= Decimal("2")
