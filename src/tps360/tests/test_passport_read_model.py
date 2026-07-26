import pytest

from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
)
from tps360.community.domain.passport_read_model import (
    CommunityPassportReadModel,
    InfrastructureItemReadModel,
)
from tps360.core.exceptions import DomainRuleViolation


def test_passport_read_model_creation() -> None:
    item = InfrastructureItemReadModel(
        id="infra_poultry_1",
        name="Птахофабрика Березнегувате",
        category=CriticalInfrastructureCategory.POULTRY_FARM,
        latitude=47.3,
        longitude=32.8,
    )
    assert item.osm_key == "farmyard"
    assert item.osm_value == "poultry"

    passport = CommunityPassportReadModel(
        community_id="comm_1",
        name="Громада 1",
        official_code="UA123456",
        region="Миколаївська область",
        district="Баштанський район",
        area_sq_km=500.0,
        total_population=12000,
        preparedness_score=72.0,
        maturity_level="Integrated",
        vulnerable_population_total=2000,
        infrastructure_items=(item,),
    )

    assert passport.critical_infrastructure_count == 1
    poultry_items = passport.get_items_by_category(CriticalInfrastructureCategory.POULTRY_FARM)
    assert len(poultry_items) == 1
    assert poultry_items[0].id == "infra_poultry_1"


def test_invalid_coordinates_raises_error() -> None:
    with pytest.raises(DomainRuleViolation, match="Invalid latitude or longitude"):
        InfrastructureItemReadModel(
            id="infra_invalid",
            name="Invalid Pos",
            category=CriticalInfrastructureCategory.POWER_LINE,
            latitude=120.0,
            longitude=30.0,
        )
