from __future__ import annotations

from dataclasses import dataclass

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.task_directive import DirectiveStatus, TaskDirective
from tps360.simulation.domain.task_execution import (
    RoundCommand,
    RoundExecutionResult,
    TaskExecutionState,
    TaskExecutionStatus,
    TaskRoundExecutionEngine,
)


@dataclass(frozen=True)
class RoundExecutionServiceResult:
    """Immutable result of processing a simulation round across tasks and directives."""

    execution_result: RoundExecutionResult
    updated_directives: tuple[TaskDirective, ...]

    @property
    def state(self) -> TaskExecutionState:
        return self.execution_result.state


class RoundExecutionService:
    """High-level orchestration service for executing simulation rounds and synchronizing directives."""

    @staticmethod
    def process_next_round(
        state: TaskExecutionState,
        directives: tuple[TaskDirective, ...],
        operation_id: str,
    ) -> RoundExecutionServiceResult:
        if any(directive.session_id != state.session_id for directive in directives):
            raise DomainRuleViolation("Directive belongs to another session.")

        next_round = state.current_round + 1
        command = RoundCommand(
            session_id=state.session_id,
            round_number=next_round,
            operation_id=operation_id,
        )

        exec_result = TaskRoundExecutionEngine.process_round(state, command)
        updated_state = exec_result.state

        synced_directives: list[TaskDirective] = []
        for directive in directives:
            if directive.task_execution_id is None or directive.is_terminal:
                synced_directives.append(directive)
                continue

            linked_task = next(
                (task for task in updated_state.tasks if task.id == directive.task_execution_id),
                None,
            )
            if linked_task is None:
                synced_directives.append(directive)
                continue

            if (
                linked_task.status is TaskExecutionStatus.COMPLETED
                and directive.status in (DirectiveStatus.ASSIGNED, DirectiveStatus.IN_PROGRESS)
            ):
                updated_dir = directive.transition(
                    DirectiveStatus.SUBMITTED,
                    round_number=next_round,
                    completion_report=f"System auto-submitted on task execution completion in round {next_round}.",
                )
                synced_directives.append(updated_dir)
            elif (
                linked_task.status is TaskExecutionStatus.FAILED
                and directive.status in (DirectiveStatus.ASSIGNED, DirectiveStatus.IN_PROGRESS, DirectiveStatus.SUBMITTED)
            ):
                updated_dir = directive.transition(
                    DirectiveStatus.REJECTED,
                    round_number=next_round,
                )
                synced_directives.append(updated_dir)
            elif (
                linked_task.status is TaskExecutionStatus.CANCELLED
                and not directive.is_terminal
            ):
                updated_dir = directive.transition(
                    DirectiveStatus.CANCELLED,
                    round_number=next_round,
                )
                synced_directives.append(updated_dir)
            else:
                synced_directives.append(directive)

        return RoundExecutionServiceResult(
            execution_result=exec_result,
            updated_directives=tuple(synced_directives),
        )
