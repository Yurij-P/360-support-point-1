from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from tps360.core.exceptions import DomainRuleViolation


class DirectiveStatus(StrEnum):
    PROPOSED = "PROPOSED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class DirectivePriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


TERMINAL_DIRECTIVE_STATUSES = frozenset({
    DirectiveStatus.VERIFIED,
    DirectiveStatus.CANCELLED,
})

ALLOWED_DIRECTIVE_TRANSITIONS = {
    DirectiveStatus.PROPOSED: frozenset({
        DirectiveStatus.ASSIGNED,
        DirectiveStatus.CANCELLED,
    }),
    DirectiveStatus.ASSIGNED: frozenset({
        DirectiveStatus.IN_PROGRESS,
        DirectiveStatus.REJECTED,
        DirectiveStatus.CANCELLED,
    }),
    DirectiveStatus.IN_PROGRESS: frozenset({
        DirectiveStatus.SUBMITTED,
        DirectiveStatus.REJECTED,
        DirectiveStatus.CANCELLED,
    }),
    DirectiveStatus.SUBMITTED: frozenset({
        DirectiveStatus.VERIFIED,
        DirectiveStatus.REJECTED,
        DirectiveStatus.CANCELLED,
    }),
    DirectiveStatus.REJECTED: frozenset({
        DirectiveStatus.IN_PROGRESS,
        DirectiveStatus.ASSIGNED,
        DirectiveStatus.CANCELLED,
    }),
    DirectiveStatus.VERIFIED: frozenset(),
    DirectiveStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class TaskDirective:
    """Immutable domain model for task contracts and role directives between facilitators and participants."""

    id: str
    session_id: str
    issuer_role_id: str
    assignee_role_id: str
    title: str
    description: str
    target_round: int
    task_execution_id: str | None = None
    status: DirectiveStatus = DirectiveStatus.PROPOSED
    priority: DirectivePriority = DirectivePriority.NORMAL
    completion_report: str | None = None
    created_at_round: int = 0
    completed_at_round: int | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.session_id:
            raise DomainRuleViolation("Task directive identifiers are required.")
        if not self.issuer_role_id or not self.assignee_role_id:
            raise DomainRuleViolation("Task directive issuer and assignee role IDs are required.")
        if not self.title.strip():
            raise DomainRuleViolation("Task directive title cannot be empty.")
        if self.target_round < 1:
            raise DomainRuleViolation("Target round must be positive.")
        if self.created_at_round < 0:
            raise DomainRuleViolation("Created at round cannot be negative.")
        if self.completed_at_round is not None and self.completed_at_round < self.created_at_round:
            raise DomainRuleViolation("Completed round cannot be earlier than created round.")
        if self.status in TERMINAL_DIRECTIVE_STATUSES and self.completed_at_round is None:
            raise DomainRuleViolation("Terminal directives require a completion round.")
        if self.status not in TERMINAL_DIRECTIVE_STATUSES and self.completed_at_round is not None:
            raise DomainRuleViolation("Non-terminal directives cannot have a completion round.")
        if self.status is DirectiveStatus.SUBMITTED and not (self.completion_report and self.completion_report.strip()):
            raise DomainRuleViolation("Submitted directive requires a non-empty completion report.")

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_DIRECTIVE_STATUSES

    def transition(
        self,
        new_status: DirectiveStatus,
        round_number: int,
        completion_report: str | None = None,
    ) -> TaskDirective:
        if new_status not in ALLOWED_DIRECTIVE_TRANSITIONS[self.status]:
            raise DomainRuleViolation(
                f"Invalid directive transition: {self.status} -> {new_status}."
            )
        if round_number < self.created_at_round:
            raise DomainRuleViolation("Transition round cannot precede creation round.")

        report_to_set = completion_report if completion_report is not None else self.completion_report
        if new_status is DirectiveStatus.SUBMITTED and not (report_to_set and report_to_set.strip()):
            raise DomainRuleViolation("Submitted directive requires a non-empty completion report.")

        completed_round = round_number if new_status in TERMINAL_DIRECTIVE_STATUSES else None

        return replace(
            self,
            status=new_status,
            completion_report=report_to_set,
            completed_at_round=completed_round,
        )
