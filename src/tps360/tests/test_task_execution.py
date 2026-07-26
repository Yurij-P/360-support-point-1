from decimal import Decimal

import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.participant_capability import (
    ResourceAvailability,
    ResourceCommitmentRequirement,
    ResourceStateSnapshot,
)
from tps360.simulation.domain.task_execution import (
    ExecutionResourceState,
    RoundCommand,
    TaskExecution,
    TaskExecutionState,
    TaskExecutionStatus,
    TaskResourceAllocation,
    TaskRoundExecutionEngine,
    TransitionType,
)

SESSION = "session_x"


def snapshot(resource_id: str, quantity: float = 10, capacity: float | None = None) -> ResourceStateSnapshot:
    return ResourceStateSnapshot(
        resource_id=resource_id,
        availability=ResourceAvailability.AVAILABLE,
        current_quantity=quantity,
        available_quantity=quantity,
        committed_quantity=0,
        current_capacity=capacity,
        available_capacity=capacity,
        committed_capacity=0 if capacity is not None else None,
    )


def task(
    task_id: str = "task_x",
    planned: str = "5",
    productivity: str = "2",
    status: TaskExecutionStatus = TaskExecutionStatus.PLANNED,
    completed: str = "0",
) -> TaskExecution:
    return TaskExecution(
        id=task_id,
        session_id=SESSION,
        planned_work=Decimal(planned),
        productivity_per_round=Decimal(productivity),
        status=status,
        completed_work=Decimal(completed),
        start_round=0 if status is TaskExecutionStatus.ACTIVE else None,
    )


def state_with(*tasks: TaskExecution, resource_ids: tuple[str, ...] = ("resource_x",)) -> TaskExecutionState:
    state = TaskRoundExecutionEngine.state_from_snapshots(
        SESSION, tuple(snapshot(resource_id) for resource_id in resource_ids)
    )
    for item in tasks:
        state = TaskRoundExecutionEngine.add_task(state, item)
    return state


def active_state(
    task_id: str = "task_x",
    planned: str = "5",
    productivity: str = "2",
) -> TaskExecutionState:
    state = state_with(task(task_id, planned, productivity))
    return TaskRoundExecutionEngine.activate(
        state,
        task_id,
        0,
        (TaskResourceAllocation("requirement_x", "resource_x", quantity=1),),
    ).state


def process(state: TaskExecutionState, round_number: int = 1, operation: str = "op_x"):
    return TaskRoundExecutionEngine.process_round(
        state, RoundCommand(SESSION, round_number, operation)
    )


def test_valid_planned_task_is_created() -> None:
    item = task()
    assert item.status is TaskExecutionStatus.PLANNED
    assert item.remaining_work == Decimal("5")


@pytest.mark.parametrize("planned,completed", [("0", "0"), ("-1", "0"), ("5", "6"), ("5", "-1")])
def test_invalid_work_is_rejected(planned: str, completed: str) -> None:
    with pytest.raises(DomainRuleViolation):
        task(planned=planned, completed=completed)


def test_activation_validates_existing_resource_requirements() -> None:
    requirement = ResourceCommitmentRequirement(
        id="requirement_x", resource_ids=("resource_x",), minimum_quantity=3
    )
    state = state_with(TaskExecution(
        id="task_x", session_id=SESSION, planned_work=5, productivity_per_round=2,
        resource_requirements=(requirement,)
    ))
    with pytest.raises(DomainRuleViolation):
        TaskRoundExecutionEngine.activate(
            state, "task_x", 0,
            (TaskResourceAllocation("requirement_x", "resource_x", quantity=2),),
        )

def test_activation_reserves_resources_and_records_transition() -> None:
    result = TaskRoundExecutionEngine.activate(
        state_with(task()),
        "task_x",
        0,
        (TaskResourceAllocation("requirement_x", "resource_x", quantity=3),),
    )
    resource = result.state.resource("resource_x")
    assert result.state.task("task_x").status is TaskExecutionStatus.ACTIVE
    assert resource.available_quantity == Decimal("7")
    assert resource.committed_quantity == Decimal("3")
    assert result.transitions[0].transition_type is TransitionType.ACTIVATED


def test_unavailable_resource_cannot_be_reserved() -> None:
    state = TaskRoundExecutionEngine.state_from_snapshots(
        SESSION,
        (ResourceStateSnapshot(
            resource_id="resource_x",
            current_quantity=10,
            available_quantity=10,
            availability=ResourceAvailability.UNAVAILABLE,
        ),),
    )
    state = TaskRoundExecutionEngine.add_task(state, task())
    with pytest.raises(DomainRuleViolation):
        TaskRoundExecutionEngine.activate(
            state, "task_x", 0,
            (TaskResourceAllocation("req", "resource_x", quantity=1),),
        )

def test_activation_is_atomic_when_second_resource_is_insufficient() -> None:
    state = state_with(task(), resource_ids=("resource_a", "resource_b"))
    allocations = (
        TaskResourceAllocation("requirement_a", "resource_a", quantity=2),
        TaskResourceAllocation("requirement_b", "resource_b", quantity=11),
    )
    with pytest.raises(DomainRuleViolation):
        TaskRoundExecutionEngine.activate(state, "task_x", 0, allocations)
    assert state.resource("resource_a").available_quantity == Decimal("10")
    assert state.task("task_x").status is TaskExecutionStatus.PLANNED


def test_double_reservation_is_rejected() -> None:
    state = active_state()
    with pytest.raises(DomainRuleViolation):
        TaskRoundExecutionEngine.activate(
            state,
            "task_x",
            0,
            (TaskResourceAllocation("requirement_x", "resource_x", quantity=1),),
        )


def test_active_task_progresses_for_one_round() -> None:
    result = process(active_state())
    item = result.state.task("task_x")
    assert item.completed_work == Decimal("2")
    assert item.status is TaskExecutionStatus.ACTIVE
    assert result.transitions[0].progress_delta == Decimal("2")


def test_partial_execution_spans_multiple_rounds() -> None:
    first = process(active_state(), 1, "op_1")
    second = process(first.state, 2, "op_2")
    assert second.state.task("task_x").completed_work == Decimal("4")
    assert second.state.task("task_x").status is TaskExecutionStatus.ACTIVE


def test_completion_caps_progress_and_releases_resources() -> None:
    result = process(active_state(planned="3", productivity="5"))
    item = result.state.task("task_x")
    resource = result.state.resource("resource_x")
    assert item.completed_work == Decimal("3")
    assert item.status is TaskExecutionStatus.COMPLETED
    assert resource.available_quantity == Decimal("10")
    assert resource.committed_quantity == Decimal("0")
    assert result.transitions[0].transition_type is TransitionType.COMPLETED


def test_paused_task_does_not_progress_and_keeps_reservation() -> None:
    paused = TaskRoundExecutionEngine.change_status(
        active_state(), "task_x", TaskExecutionStatus.PAUSED, 0
    ).state
    result = process(paused)
    assert result.state.task("task_x").completed_work == Decimal("0")
    assert result.state.resource("resource_x").committed_quantity == Decimal("1")


def test_paused_task_can_resume() -> None:
    paused = TaskRoundExecutionEngine.change_status(
        active_state(), "task_x", TaskExecutionStatus.PAUSED, 0
    ).state
    resumed = TaskRoundExecutionEngine.change_status(
        paused, "task_x", TaskExecutionStatus.ACTIVE, 1
    ).state
    assert resumed.task("task_x").status is TaskExecutionStatus.ACTIVE
    assert resumed.task("task_x").completed_work == Decimal("0")


@pytest.mark.parametrize("terminal", [
    TaskExecutionStatus.COMPLETED,
    TaskExecutionStatus.FAILED,
    TaskExecutionStatus.CANCELLED,
])
def test_terminal_tasks_do_not_progress(terminal: TaskExecutionStatus) -> None:
    state = active_state(planned="2", productivity="2")
    if terminal is TaskExecutionStatus.COMPLETED:
        terminal_state = process(state).state
    else:
        terminal_state = TaskRoundExecutionEngine.change_status(state, "task_x", terminal, 0).state
    result = process(terminal_state, 2 if terminal is TaskExecutionStatus.COMPLETED else 1, "op_2")
    assert result.state.task("task_x").status is terminal
    assert result.transitions == ()


@pytest.mark.parametrize("terminal", [
    TaskExecutionStatus.COMPLETED,
    TaskExecutionStatus.FAILED,
    TaskExecutionStatus.CANCELLED,
])
def test_terminal_transition_releases_resources(terminal: TaskExecutionStatus) -> None:
    state = active_state(planned="2", productivity="2")
    if terminal is TaskExecutionStatus.COMPLETED:
        result = process(state)
    else:
        result = TaskRoundExecutionEngine.change_status(state, "task_x", terminal, 0)
    assert result.state.resource("resource_x").committed_quantity == Decimal("0")


def test_invalid_transition_does_not_change_state() -> None:
    state = active_state()
    with pytest.raises(DomainRuleViolation):
        TaskRoundExecutionEngine.change_status(
            state, "task_x", TaskExecutionStatus.PLANNED, 0
        )
    assert state.task("task_x").status is TaskExecutionStatus.ACTIVE
    assert state.resource("resource_x").committed_quantity == Decimal("1")


def test_repeated_round_is_idempotent() -> None:
    first = process(active_state(), 1, "op_1")
    replay = process(first.state, 1, "op_1")
    assert replay.idempotent_replay is True
    assert replay.state == first.state
    assert replay.transitions == first.transitions


def test_repeated_round_does_not_duplicate_journal() -> None:
    first = process(active_state(), 1, "op_1")
    replay = process(first.state, 1, "op_1")
    assert len(replay.state.transitions) == 2


def test_missing_or_reverse_round_is_rejected() -> None:
    state = active_state()
    with pytest.raises(DomainRuleViolation):
        process(state, 2, "op_2")
    first = process(state, 1, "op_1")
    with pytest.raises(DomainRuleViolation):
        process(first.state, 1, "op_other")


def test_multiple_tasks_have_stable_order() -> None:
    state = state_with(task("task_b"), task("task_a"))
    state = TaskRoundExecutionEngine.activate(
        state, "task_b", 0, (TaskResourceAllocation("req_b", "resource_x", quantity=1),)
    ).state
    state = TaskRoundExecutionEngine.activate(
        state, "task_a", 0, (TaskResourceAllocation("req_a", "resource_x", quantity=1),)
    ).state
    result = process(state)
    assert [item.task_id for item in result.transitions] == ["task_a", "task_b"]
    assert [item.order for item in result.transitions] == [2, 3]


def test_same_input_produces_same_deterministic_result() -> None:
    first = process(active_state(), 1, "op_1")
    second = process(active_state(), 1, "op_1")
    assert first.state == second.state
    assert first.transitions == second.transitions


def test_input_snapshots_are_not_mutated() -> None:
    source = snapshot("resource_x")
    original = (source.current_quantity, source.available_quantity)
    TaskRoundExecutionEngine.activate(
        state_with(task()), "task_x", 0,
        (TaskResourceAllocation("req", "resource_x", quantity=2),),
    )
    assert (source.current_quantity, source.available_quantity) == original


def test_resource_invariants_reject_invalid_snapshot() -> None:
    with pytest.raises(DomainRuleViolation):
        ExecutionResourceState(
            "resource_x",
            current_quantity=Decimal("1"),
            available_quantity=Decimal("2"),
        )


def test_resource_release_cannot_happen_twice() -> None:
    state = active_state()
    released = TaskRoundExecutionEngine.change_status(
        state, "task_x", TaskExecutionStatus.CANCELLED, 0
    ).state
    with pytest.raises(DomainRuleViolation):
        TaskRoundExecutionEngine.change_status(
            released, "task_x", TaskExecutionStatus.CANCELLED, 0
        )


def test_zero_productivity_active_task_fails_atomically() -> None:
    state = active_state(productivity="0")
    with pytest.raises(DomainRuleViolation):
        process(state)
    assert state.current_round == 0
    assert state.task("task_x").completed_work == Decimal("0")


def test_non_round_state_changes_are_explicit_and_do_not_advance_clock() -> None:
    result = TaskRoundExecutionEngine.change_status(
        active_state(), "task_x", TaskExecutionStatus.PAUSED, 0
    )
    assert result.state.current_round == 0


def test_domain_is_scenario_neutral() -> None:
    state = state_with(task("arbitrary_task"))
    assert state.task("arbitrary_task").session_id == SESSION









def test_committed_resource_state_cannot_exceed_total() -> None:
    with pytest.raises(DomainRuleViolation):
        ExecutionResourceState(
            "resource_x",
            availability=ResourceAvailability.AVAILABLE,
            current_quantity=Decimal("1"),
            available_quantity=Decimal("0"),
            committed_quantity=Decimal("2"),
        )



