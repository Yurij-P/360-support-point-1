import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.time_dilation import (
    CrisisVelocity,
    SimulationRoundClock,
)
from tps360.simulation.services.ai_crisis_copilot import (
    AICrisisCopilotService,
    CopilotInputContext,
)

SESSION = "session_copilot_open_test"


def test_copilot_open_custom_crisis_with_osint_feed() -> None:
    clock = SimulationRoundClock(real_round_minutes=15, velocity=CrisisVelocity.MODERATE)
    context = CopilotInputContext(
        session_id=SESSION,
        current_round=1,
        crisis_type="Смерч у Степовому районі та пошкодження ліній",
        clock=clock,
        official_sources_feed=(
            "Зведення ДСНС: 4 населених пункти без світла",
            "Офіційний Telegram ОВА: повалено 35 дерев",
        ),
    )

    result = AICrisisCopilotService.generate_round_proposal(context)
    assert result.session_id == SESSION
    assert result.round_number == 1
    assert "Смерч у Степовому районі" in result.narrative_summary
    assert "Зведення ДСНС" in result.narrative_summary
    assert len(result.suggested_directives) == 1


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
