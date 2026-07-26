from decimal import Decimal

import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.participant_capability import (
    ResourceAvailability,
    ResourceStateSnapshot,
)
from tps360.simulation.domain.task_directive import (
    DirectiveStatus,
    TaskDirective,
)
from tps360.simulation.domain.task_execution import (
    TaskExecution,
    TaskExecutionState,
    TaskExecutionStatus,
    TaskResourceAllocation,
    TaskRoundExecutionEngine,
)
from tps360.simulation.services.round_execution_service import RoundExecutionService

SESSION = "session_round_test"


def setup_test_state() -> TaskExecutionState:
    snapshot = ResourceStateSnapshot(
        resource_id="res_power",
        availability=ResourceAvailability.AVAILABLE,
        current_quantity=10,
        available_quantity=10,
        committed_quantity=0,
    )
    state = TaskRoundExecutionEngine.state_from_snapshots(SESSION, (snapshot,))
    task = TaskExecution(
        id="task_generator",
        session_id=SESSION,
        planned_work=Decimal("4"),
        productivity_per_round=Decimal("2"),
        status=TaskExecutionStatus.PLANNED,
    )
    state = TaskRoundExecutionEngine.add_task(state, task)
    active_state = TaskRoundExecutionEngine.activate(
        state,
        "task_generator",
        0,
        (TaskResourceAllocation("req_power", "res_power", quantity=2),),
    ).state
    return active_state


def test_process_next_round_advances_clock_and_task_progress() -> None:
    state = setup_test_state()
    directive = TaskDirective(
        id="dir_001",
        session_id=SESSION,
        issuer_role_id="facilitator",
        assignee_role_id="chief_engineer",
        title="Deploy generators",
        description="Power critical hospital systems",
        target_round=3,
        task_execution_id="task_generator",
        status=DirectiveStatus.IN_PROGRESS,
    )

    res = RoundExecutionService.process_next_round(
        state, (directive,), operation_id="op_round_1"
    )

    assert res.state.current_round == 1
    assert res.state.task("task_generator").completed_work == Decimal("2")
    assert res.updated_directives[0].status is DirectiveStatus.IN_PROGRESS


def test_process_next_round_auto_submits_directive_on_task_completion() -> None:
    state = setup_test_state()
    directive = TaskDirective(
        id="dir_001",
        session_id=SESSION,
        issuer_role_id="facilitator",
        assignee_role_id="chief_engineer",
        title="Deploy generators",
        description="Power critical hospital systems",
        target_round=3,
        task_execution_id="task_generator",
        status=DirectiveStatus.IN_PROGRESS,
    )

    res1 = RoundExecutionService.process_next_round(state, (directive,), operation_id="op_round_1")
    res2 = RoundExecutionService.process_next_round(res1.state, res1.updated_directives, operation_id="op_round_2")

    assert res2.state.task("task_generator").status is TaskExecutionStatus.COMPLETED
    final_directive = res2.updated_directives[0]
    assert final_directive.status is DirectiveStatus.SUBMITTED
    assert "System auto-submitted" in (final_directive.completion_report or "")


def test_directive_from_another_session_is_rejected() -> None:
    state = setup_test_state()
    alien_directive = TaskDirective(
        id="dir_alien",
        session_id="alien_session",
        issuer_role_id="facilitator",
        assignee_role_id="chief_engineer",
        title="Alien mission",
        description="Invalid session",
        target_round=2,
    )

    with pytest.raises(DomainRuleViolation, match="Directive belongs to another session"):
        RoundExecutionService.process_next_round(state, (alien_directive,), "op_err")
