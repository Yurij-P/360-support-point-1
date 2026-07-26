import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.task_directive import (
    DirectivePriority,
    DirectiveStatus,
    TaskDirective,
)


def create_directive(
    directive_id: str = "dir_001",
    session_id: str = "session_001",
    issuer: str = "facilitator",
    assignee: str = "head_of_emergency",
    title: str = "Deploy Emergency Generators",
    description: str = "Provide backup power to municipal hospital",
    target_round: int = 3,
    status: DirectiveStatus = DirectiveStatus.PROPOSED,
    priority: DirectivePriority = DirectivePriority.HIGH,
    created_at: int = 1,
    completed_at: int | None = None,
    completion_report: str | None = None,
) -> TaskDirective:
    return TaskDirective(
        id=directive_id,
        session_id=session_id,
        issuer_role_id=issuer,
        assignee_role_id=assignee,
        title=title,
        description=description,
        target_round=target_round,
        status=status,
        priority=priority,
        created_at_round=created_at,
        completed_at_round=completed_at,
        completion_report=completion_report,
    )


def test_valid_task_directive_created() -> None:
    directive = create_directive()
    assert directive.id == "dir_001"
    assert directive.status is DirectiveStatus.PROPOSED
    assert directive.priority is DirectivePriority.HIGH
    assert not directive.is_terminal


def test_empty_identifiers_raise_error() -> None:
    with pytest.raises(DomainRuleViolation, match="Task directive identifiers are required"):
        create_directive(directive_id="")

    with pytest.raises(DomainRuleViolation, match="Task directive issuer and assignee role IDs are required"):
        create_directive(issuer="")


def test_empty_title_raises_error() -> None:
    with pytest.raises(DomainRuleViolation, match="title cannot be empty"):
        create_directive(title="   ")


def test_invalid_target_round_raises_error() -> None:
    with pytest.raises(DomainRuleViolation, match="Target round must be positive"):
        create_directive(target_round=0)


def test_invalid_completed_round_raises_error() -> None:
    with pytest.raises(DomainRuleViolation, match="Completed round cannot be earlier than created round"):
        create_directive(
            status=DirectiveStatus.VERIFIED,
            created_at=2,
            completed_at=1,
        )


def test_terminal_status_without_completed_round_raises_error() -> None:
    with pytest.raises(DomainRuleViolation, match="Terminal directives require a completion round"):
        create_directive(status=DirectiveStatus.VERIFIED, completed_at=None)


def test_directive_happy_path_transitions() -> None:
    d0 = create_directive(created_at=1, target_round=5)
    assert d0.status is DirectiveStatus.PROPOSED

    # 1. Assign
    d1 = d0.transition(DirectiveStatus.ASSIGNED, round_number=1)
    assert d1.status is DirectiveStatus.ASSIGNED

    # 2. In Progress
    d2 = d1.transition(DirectiveStatus.IN_PROGRESS, round_number=2)
    assert d2.status is DirectiveStatus.IN_PROGRESS

    # 3. Submit with report
    d3 = d2.transition(
        DirectiveStatus.SUBMITTED,
        round_number=3,
        completion_report="2 generators deployed and operational",
    )
    assert d3.status is DirectiveStatus.SUBMITTED
    assert d3.completion_report == "2 generators deployed and operational"

    # 4. Verify (Terminal)
    d4 = d3.transition(DirectiveStatus.VERIFIED, round_number=4)
    assert d4.status is DirectiveStatus.VERIFIED
    assert d4.is_terminal
    assert d4.completed_at_round == 4


def test_submission_without_report_raises_error() -> None:
    d = create_directive().transition(DirectiveStatus.ASSIGNED, 1).transition(DirectiveStatus.IN_PROGRESS, 2)
    with pytest.raises(DomainRuleViolation, match="Submitted directive requires a non-empty completion report"):
        d.transition(DirectiveStatus.SUBMITTED, round_number=3, completion_report="")


def test_rejection_and_reworking_flow() -> None:
    d = (
        create_directive()
        .transition(DirectiveStatus.ASSIGNED, 1)
        .transition(DirectiveStatus.IN_PROGRESS, 2)
        .transition(DirectiveStatus.SUBMITTED, 3, completion_report="Initial draft report")
    )

    # Reject
    rejected = d.transition(DirectiveStatus.REJECTED, round_number=3)
    assert rejected.status is DirectiveStatus.REJECTED

    # Move back to in progress
    reworking = rejected.transition(DirectiveStatus.IN_PROGRESS, round_number=4)
    assert reworking.status is DirectiveStatus.IN_PROGRESS


def test_cancellation_flow() -> None:
    d = create_directive(created_at=1)
    cancelled = d.transition(DirectiveStatus.CANCELLED, round_number=2)
    assert cancelled.status is DirectiveStatus.CANCELLED
    assert cancelled.is_terminal
    assert cancelled.completed_at_round == 2


def test_invalid_direct_transition_raises_error() -> None:
    d = create_directive()  # PROPOSED
    with pytest.raises(DomainRuleViolation, match="Invalid directive transition"):
        d.transition(DirectiveStatus.VERIFIED, round_number=2)
