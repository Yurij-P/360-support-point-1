import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.geospatial.value_objects import BoundingBox
from tps360.simulation.domain.time_dilation import (
    CrisisVelocity,
    SimulationRoundClock,
)
from tps360.simulation.services.ai_crisis_copilot import (
    AICrisisCopilotService,
    CopilotInputContext,
    EmpiricalCrisisIncidentFact,
)

SESSION = "session_copilot_osm_spatial_test"


def test_copilot_open_crisis_with_osm_spatial_boundary() -> None:
    clock = SimulationRoundClock(real_round_minutes=15, velocity=CrisisVelocity.MODERATE)
    osm_bbox = BoundingBox(47.0, 32.0, 48.0, 33.0)

    context = CopilotInputContext(
        session_id=SESSION,
        current_round=1,
        crisis_type="Смерч у Степовому районі та пошкодження ліній",
        clock=clock,
        community_boundary_bbox=osm_bbox,
        osm_relation_id="osm_relation_bereznehuvate_123",
        official_sources_feed=(
            "Зведення ДСНС: 4 населених пункти без світла",
            "Офіційний Telegram ОВА: повалено 35 дерев",
        ),
    )

    result = AICrisisCopilotService.generate_round_proposal(context)
    assert result.session_id == SESSION
    assert result.round_number == 1
    assert result.is_spatial_bounded_by_osm is True
    assert "OpenStreetMap" in result.narrative_summary
    assert "min_lat=47.000" in result.narrative_summary
    assert "Зведення ДСНС" in result.narrative_summary
    assert len(result.suggested_directives) == 1
    assert "OpenStreetMap" in result.suggested_directives[0].description


def test_copilot_empirical_fact_double_tap_and_ammo_detonation() -> None:
    clock = SimulationRoundClock(real_round_minutes=15, velocity=CrisisVelocity.FAST)
    fact1 = EmpiricalCrisisIncidentFact(
        incident_id="fact_double_tap_1",
        fact_description="Повторний ракетний удар по об'єкту під час гасіння пожежниками ДСНС",
        source_attribution="Оперативне зведення ДСНС",
        cascade_hazard_type="SECONDARY_STRIKE_DOUBLE_TAP",
        hazard_radius_km=0.5,
    )
    fact2 = EmpiricalCrisisIncidentFact(
        incident_id="fact_ammo_truck_1",
        fact_description="Влучання БПЛА у військовий вантажний транспорт з БК та розліт снарядів",
        source_attribution="Генеральний Штаб / ЗМІ",
        cascade_hazard_type="AMMO_DETONATION_RADIUS_2KM",
        hazard_radius_km=2.0,
    )

    context = CopilotInputContext(
        session_id=SESSION,
        current_round=2,
        crisis_type="Ракетно-дроновий обстріл та детонація БК",
        clock=clock,
        empirical_facts=(fact1, fact2),
    )

    result = AICrisisCopilotService.generate_round_proposal(context)
    assert "Підтверджені факти реальних подій" in result.narrative_summary
    assert "SECONDARY_STRIKE_DOUBLE_TAP" in result.narrative_summary
    assert "2.0 км" in result.narrative_summary
    # Verify double-tap responder safety directive was generated
    directive_titles = [d.title for d in result.suggested_directives]
    assert any("протокол повторного удару" in title for title in directive_titles)


def test_copilot_epizootic_custom_crisis() -> None:
    clock = SimulationRoundClock(real_round_minutes=20, velocity=CrisisVelocity.SLOW_MAX)
    context = CopilotInputContext(
        session_id=SESSION,
        current_round=3,
        crisis_type="Спалах африканської чуми свиней (АЧС)",
        clock=clock,
    )

    result = AICrisisCopilotService.generate_round_proposal(context)
    assert result.simulated_hours_passed == 30.0
    assert result.is_spatial_bounded_by_osm is True
    assert "АЧС" in result.suggested_inject_title
    directive = result.suggested_directives[0]
    assert directive.assignee_role_id == "chief_sanitary_inspector"


def test_invalid_copilot_context_raises_error() -> None:
    clock = SimulationRoundClock(real_round_minutes=10, velocity=CrisisVelocity.MODERATE)
    with pytest.raises(DomainRuleViolation, match="requires session_id and crisis_type"):
        CopilotInputContext(
            session_id="",
            current_round=1,
            crisis_type="Test",
            clock=clock,
        )
