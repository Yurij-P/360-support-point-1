
import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.task_directive import (
    DirectivePriority,
    DirectiveStatus,
    TaskDirective,
)
from tps360.simulation.domain.time_dilation import (
    CrisisVelocity,
    SimulationRoundClock,
)
from tps360.simulation.services.ai_crisis_copilot import (
    AICrisisCopilotService,
    CopilotInputContext,
)

SESSION = "session_copilot_test"


def test_copilot_proposal_for_cholera_outbreak() -> None:
    clock = SimulationRoundClock(real_round_minutes=15, velocity=CrisisVelocity.MODERATE)
    context = CopilotInputContext(
        session_id=SESSION,
        current_round=2,
        crisis_type="CHOLERA",
        clock=clock,
    )

    result = AICrisisCopilotService.generate_round_proposal(context)
    assert result.session_id == SESSION
    assert result.round_number == 2
    assert result.simulated_hours_passed == 15.0  # 15 real mins * 60 = 900 sim mins = 15 hrs
    assert "CHOLERA" in result.suggested_inject_title
    assert len(result.suggested_directives) == 1
    directive = result.suggested_directives[0]
    assert directive.assignee_role_id == "chief_medical_officer"
    assert directive.priority is DirectivePriority.HIGH


def test_copilot_proposal_for_livestock_epizootic() -> None:
    clock = SimulationRoundClock(real_round_minutes=20, velocity=CrisisVelocity.SLOW_MAX)
    context = CopilotInputContext(
        session_id=SESSION,
        current_round=3,
        crisis_type="LIVESTOCK_MORTALITY",
        clock=clock,
    )

    result = AICrisisCopilotService.generate_round_proposal(context)
    assert result.simulated_hours_passed == 30.0  # 20 real mins * 90 = 1800 sim mins = 30 hrs
    assert "LIVESTOCK_MORTALITY" in result.suggested_inject_title
    directive = result.suggested_directives[0]
    assert directive.assignee_role_id == "chief_veterinary_inspector"
    assert directive.priority is DirectivePriority.CRITICAL


def test_copilot_proposal_incorporates_submitted_reports() -> None:
    clock = SimulationRoundClock(real_round_minutes=10, velocity=CrisisVelocity.FAST)
    report_directive = TaskDirective(
        id="d_report",
        session_id=SESSION,
        issuer_role_id="facilitator",
        assignee_role_id="chief_engineer",
        title="Generator status",
        description="Check power",
        target_round=1,
        status=DirectiveStatus.SUBMITTED,
        completion_report="Generator connected to hospital sub-station.",
    )
    context = CopilotInputContext(
        session_id=SESSION,
        current_round=1,
        crisis_type="FIRE",
        clock=clock,
        submitted_directives=(report_directive,),
    )

    result = AICrisisCopilotService.generate_round_proposal(context)
    assert "Generator connected to hospital sub-station" in result.narrative_summary


def test_invalid_copilot_context_raises_error() -> None:
    clock = SimulationRoundClock(real_round_minutes=10, velocity=CrisisVelocity.MODERATE)
    with pytest.raises(DomainRuleViolation, match="requires session_id and crisis_type"):
        CopilotInputContext(
            session_id="",
            current_round=1,
            crisis_type="FIRE",
            clock=clock,
        )
