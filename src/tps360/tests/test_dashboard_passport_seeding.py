from decimal import Decimal

from tps360.community.domain.passport_read_model import CommunityPassportReadModel
from tps360.simulation.services.resource_estimator import estimate_role_resources
from tps360.simulation.services.role_dashboard_service import RoleDashboardService


def _passport(population: int = 15000) -> CommunityPassportReadModel:
    return CommunityPassportReadModel(
        community_id="ua00000000000000000",
        name="Тестова громада",
        official_code="UA00000000000000000",
        region="Область",
        district="Район",
        area_sq_km=120.0,
        total_population=population,
        preparedness_score=70.0,
        maturity_level="Integrated",
        vulnerable_population_total=2700,
    )


def test_dashboard_seeds_from_passport_when_bound() -> None:
    service = RoleDashboardService()
    passport = _passport()
    service.set_session_passport("s_passport", passport)

    workspace = service.get_role_workspace("s_passport", "communal-utility")
    expected = estimate_role_resources("communal-utility", passport)
    assert workspace.initial_resources == {k: Decimal(str(v)) for k, v in expected.items()}


def test_dashboard_falls_back_to_static_seeds_without_passport() -> None:
    service = RoleDashboardService()
    workspace = service.get_role_workspace("s_static", "emerg-dsns")
    # static placeholder seed value
    assert workspace.initial_resources["fire_trucks"] == Decimal("10")
