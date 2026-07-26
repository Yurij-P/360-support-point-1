from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import NAMESPACE_URL, uuid5

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.participant_capability import (
    ResourceAvailability,
    ResourceCommitmentRequirement,
    ResourceStateSnapshot,
)


class TaskExecutionStatus(StrEnum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TransitionType(StrEnum):
    ACTIVATED = "activated"
    PAUSED = "paused"
    RESUMED = "resumed"
    PROGRESSED = "progressed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransitionReason(StrEnum):
    EXPLICIT_COMMAND = "explicit_command"
    ROUND_PROGRESS = "round_progress"
    WORK_COMPLETE = "work_complete"
    RESOURCE_RELEASED = "resource_released"


TERMINAL = frozenset({
    TaskExecutionStatus.COMPLETED,
    TaskExecutionStatus.FAILED,
    TaskExecutionStatus.CANCELLED,
})
ALLOWED_TRANSITIONS = {
    TaskExecutionStatus.PLANNED: frozenset({TaskExecutionStatus.ACTIVE, TaskExecutionStatus.CANCELLED}),
    TaskExecutionStatus.ACTIVE: frozenset({
        TaskExecutionStatus.PAUSED,
        TaskExecutionStatus.COMPLETED,
        TaskExecutionStatus.FAILED,
        TaskExecutionStatus.CANCELLED,
    }),
    TaskExecutionStatus.PAUSED: frozenset({
        TaskExecutionStatus.ACTIVE,
        TaskExecutionStatus.FAILED,
        TaskExecutionStatus.CANCELLED,
    }),
    TaskExecutionStatus.COMPLETED: frozenset(),
    TaskExecutionStatus.FAILED: frozenset(),
    TaskExecutionStatus.CANCELLED: frozenset(),
}


def decimal(value: Decimal | float | int | str, label: str) -> Decimal:
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DomainRuleViolation(f"{label} must be a finite number.") from exc
    if not result.is_finite():
        raise DomainRuleViolation(f"{label} must be a finite number.")
    return result


def non_negative(value: Decimal, label: str) -> None:
    if value < 0:
        raise DomainRuleViolation(f"{label} cannot be negative.")


@dataclass(frozen=True)
class TaskResourceAllocation:
    requirement_id: str
    resource_id: str
    quantity: Decimal = Decimal("0")
    capacity: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.requirement_id or not self.resource_id:
            raise DomainRuleViolation("Task resource allocation identifiers are required.")
        quantity = decimal(self.quantity, "Allocated quantity")
        capacity = decimal(self.capacity, "Allocated capacity")
        non_negative(quantity, "Allocated quantity")
        non_negative(capacity, "Allocated capacity")
        if quantity == 0 and capacity == 0:
            raise DomainRuleViolation("Allocation must reserve quantity or capacity.")
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "capacity", capacity)


@dataclass(frozen=True)
class ResourceReservation:
    resource_id: str
    owner_task_id: str
    quantity: Decimal
    capacity: Decimal

    def __post_init__(self) -> None:
        if not self.resource_id or not self.owner_task_id:
            raise DomainRuleViolation("Resource reservation identifiers are required.")
        quantity = decimal(self.quantity, "Reserved quantity")
        capacity = decimal(self.capacity, "Reserved capacity")
        non_negative(abs(quantity), "Reserved quantity")
        non_negative(abs(capacity), "Reserved capacity")
        if quantity == 0 and capacity == 0:
            raise DomainRuleViolation("Reservation must change quantity or capacity.")
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "capacity", capacity)


@dataclass(frozen=True)
class ExecutionResourceState:
    """Immutable resource state with single-owner reservations."""
    resource_id: str
    availability: ResourceAvailability = ResourceAvailability.UNKNOWN
    current_quantity: Decimal | None = None
    available_quantity: Decimal | None = None
    committed_quantity: Decimal | None = None
    current_capacity: Decimal | None = None
    available_capacity: Decimal | None = None
    committed_capacity: Decimal | None = None
    reservations: tuple[ResourceReservation, ...] = ()

    @classmethod
    def from_snapshot(cls, snapshot: ResourceStateSnapshot) -> ExecutionResourceState:
        return cls(
            resource_id=snapshot.resource_id,
            availability=snapshot.availability,
            current_quantity=None if snapshot.current_quantity is None else decimal(snapshot.current_quantity, "current_quantity"),
            available_quantity=None if snapshot.available_quantity is None else decimal(snapshot.available_quantity, "available_quantity"),
            committed_quantity=None if snapshot.committed_quantity is None else decimal(snapshot.committed_quantity, "committed_quantity"),
            current_capacity=None if snapshot.current_capacity is None else decimal(snapshot.current_capacity, "current_capacity"),
            available_capacity=None if snapshot.available_capacity is None else decimal(snapshot.available_capacity, "available_capacity"),
            committed_capacity=None if snapshot.committed_capacity is None else decimal(snapshot.committed_capacity, "committed_capacity"),
        )

    def __post_init__(self) -> None:
        for name in (
            "current_quantity",
            "available_quantity",
            "committed_quantity",
            "current_capacity",
            "available_capacity",
            "committed_capacity",
        ):
            value = getattr(self, name)
            if value is not None:
                converted = decimal(value, name)
                non_negative(converted, name)
                object.__setattr__(self, name, converted)
        if self.committed_quantity is not None and self.current_quantity is not None:
            if self.committed_quantity > self.current_quantity:
                raise DomainRuleViolation("Committed quantity cannot exceed current quantity.")
        if self.committed_capacity is not None and self.current_capacity is not None:
            if self.committed_capacity > self.current_capacity:
                raise DomainRuleViolation("Committed capacity cannot exceed current capacity.")

        if self.available_quantity is not None and self.current_quantity is not None:
            if self.available_quantity > self.current_quantity:
                raise DomainRuleViolation("Available quantity cannot exceed current quantity.")
        if self.available_capacity is not None and self.current_capacity is not None:
            if self.available_capacity > self.current_capacity:
                raise DomainRuleViolation("Available capacity cannot exceed current capacity.")
        if any(item.resource_id != self.resource_id for item in self.reservations):
            raise DomainRuleViolation("Reservation belongs to another resource.")
        if len({item.owner_task_id for item in self.reservations}) != len(self.reservations):
            raise DomainRuleViolation("A task cannot reserve a resource twice.")

    def reservation_for(self, task_id: str) -> ResourceReservation | None:
        return next((item for item in self.reservations if item.owner_task_id == task_id), None)

    def reserve(self, reservation: ResourceReservation) -> ExecutionResourceState:
        if self.availability is not ResourceAvailability.AVAILABLE:
            raise DomainRuleViolation("Resource is not available for reservation.")
        if self.reservation_for(reservation.owner_task_id) is not None:
            raise DomainRuleViolation("Task already has a reservation for this resource.")
        if self.available_quantity is not None and reservation.quantity > self.available_quantity:
            raise DomainRuleViolation("Resource quantity is insufficient.")
        if self.available_capacity is not None and reservation.capacity > self.available_capacity:
            raise DomainRuleViolation("Resource capacity is insufficient.")
        return replace(
            self,
            available_quantity=(
                None if self.available_quantity is None
                else self.available_quantity - reservation.quantity
            ),
            available_capacity=(
                None if self.available_capacity is None
                else self.available_capacity - reservation.capacity
            ),
            committed_quantity=(
                None if self.committed_quantity is None
                else self.committed_quantity + reservation.quantity
            ),
            committed_capacity=(
                None if self.committed_capacity is None
                else self.committed_capacity + reservation.capacity
            ),
            reservations=self.reservations + (reservation,),
        )

    def release(self, task_id: str) -> ExecutionResourceState:
        reservation = self.reservation_for(task_id)
        if reservation is None:
            raise DomainRuleViolation("Resource reservation does not exist.")
        return replace(
            self,
            available_quantity=(
                None if self.available_quantity is None
                else self.available_quantity + reservation.quantity
            ),
            available_capacity=(
                None if self.available_capacity is None
                else self.available_capacity + reservation.capacity
            ),
            committed_quantity=(
                None if self.committed_quantity is None
                else self.committed_quantity - reservation.quantity
            ),
            committed_capacity=(
                None if self.committed_capacity is None
                else self.committed_capacity - reservation.capacity
            ),
            reservations=tuple(
                item for item in self.reservations if item.owner_task_id != task_id
            ),
        )


@dataclass(frozen=True)
class TaskExecution:
    id: str
    session_id: str
    planned_work: Decimal
    productivity_per_round: Decimal
    resource_requirements: tuple[ResourceCommitmentRequirement, ...] = ()
    allocations: tuple[TaskResourceAllocation, ...] = ()
    status: TaskExecutionStatus = TaskExecutionStatus.PLANNED
    completed_work: Decimal = Decimal("0")
    start_round: int | None = None
    last_processed_round: int | None = None
    completion_round: int | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.session_id:
            raise DomainRuleViolation("Task execution identifiers are required.")
        planned = decimal(self.planned_work, "Planned work")
        productivity = decimal(self.productivity_per_round, "Productivity per round")
        completed = decimal(self.completed_work, "Completed work")
        non_negative(planned, "Planned work")
        non_negative(productivity, "Productivity per round")
        non_negative(completed, "Completed work")
        if planned <= 0:
            raise DomainRuleViolation("Planned work must be greater than zero.")
        if completed > planned:
            raise DomainRuleViolation("Completed work cannot exceed planned work.")
        if self.status is TaskExecutionStatus.COMPLETED and completed != planned:
            raise DomainRuleViolation("Completed task must have completed all planned work.")
        if self.status is TaskExecutionStatus.ACTIVE and self.start_round is None:
            raise DomainRuleViolation("Active task requires a start round.")
        if self.completion_round is not None and self.status not in TERMINAL:
            raise DomainRuleViolation("Only terminal tasks have a completion round.")
        if len({item.id for item in self.resource_requirements}) != len(self.resource_requirements):
            raise DomainRuleViolation("Task resource requirements must be unique.")
        if len({item.requirement_id for item in self.allocations}) != len(self.allocations):
            raise DomainRuleViolation("Task allocation requirements must be unique.")
        object.__setattr__(self, "planned_work", planned)
        object.__setattr__(self, "productivity_per_round", productivity)
        object.__setattr__(self, "completed_work", completed)

    @property
    def remaining_work(self) -> Decimal:
        return self.planned_work - self.completed_work

    def transition(self, status: TaskExecutionStatus, round_number: int) -> TaskExecution:
        if status not in ALLOWED_TRANSITIONS[self.status]:
            raise DomainRuleViolation(f"Invalid task transition: {self.status} -> {status}.")
        if round_number < 0:
            raise DomainRuleViolation("Round number cannot be negative.")
        return replace(
            self,
            status=status,
            start_round=(
                round_number
                if status is TaskExecutionStatus.ACTIVE and self.start_round is None
                else self.start_round
            ),
            completion_round=(round_number if status in TERMINAL else None),
        )


@dataclass(frozen=True)
class ExecutionTransition:
    id: str
    session_id: str
    round_number: int
    task_id: str
    transition_type: TransitionType
    previous_status: TaskExecutionStatus
    new_status: TaskExecutionStatus
    progress_delta: Decimal
    reservation_changes: tuple[ResourceReservation, ...]
    reason: TransitionReason
    order: int


@dataclass(frozen=True)
class RoundCommand:
    session_id: str
    round_number: int
    operation_id: str

    def __post_init__(self) -> None:
        if not self.session_id or not self.operation_id:
            raise DomainRuleViolation("Round command identifiers are required.")
        if self.round_number < 1:
            raise DomainRuleViolation("Round number must be positive.")


@dataclass(frozen=True)
class ProcessedRound:
    session_id: str
    round_number: int
    operation_id: str
    transitions: tuple[ExecutionTransition, ...]


@dataclass(frozen=True)
class TaskExecutionState:
    session_id: str
    current_round: int = 0
    tasks: tuple[TaskExecution, ...] = ()
    resources: tuple[ExecutionResourceState, ...] = ()
    transitions: tuple[ExecutionTransition, ...] = ()
    processed_rounds: tuple[ProcessedRound, ...] = ()

    def __post_init__(self) -> None:
        if not self.session_id:
            raise DomainRuleViolation("Execution state requires a session identifier.")
        if self.current_round < 0:
            raise DomainRuleViolation("Current round cannot be negative.")
        if len({item.id for item in self.tasks}) != len(self.tasks):
            raise DomainRuleViolation("Execution task identifiers must be unique.")
        if len({item.resource_id for item in self.resources}) != len(self.resources):
            raise DomainRuleViolation("Execution resource identifiers must be unique.")

    def task(self, task_id: str) -> TaskExecution:
        task = next((item for item in self.tasks if item.id == task_id), None)
        if task is None:
            raise DomainRuleViolation("Execution task is unavailable.")
        return task

    def resource(self, resource_id: str) -> ExecutionResourceState:
        resource = next((item for item in self.resources if item.resource_id == resource_id), None)
        if resource is None:
            raise DomainRuleViolation("Execution resource is unavailable.")
        return resource


@dataclass(frozen=True)
class RoundExecutionResult:
    state: TaskExecutionState
    transitions: tuple[ExecutionTransition, ...]
    idempotent_replay: bool = False


class TaskRoundExecutionEngine:
    """Deterministic domain task execution engine for round-based processing.

    Engine Scope Boundary:
    - Pure, scenario-neutral domain service independent of crisis types, roles, AI/LLM,
      HTTP/APIs, database persistence, or background workers.
    - Operates purely on immutable state inputs and returns new TaskExecutionState.

    Domain Invariants:
    - Non-negative progress, valid state machine transitions (PLANNED, ACTIVE, PAUSED,
      COMPLETED, FAILED, CANCELLED). Terminal states cannot transition further.
    - Resource invariants: available/committed quantities and capacities must not exceed total capacity
      or be negative. Single-owner reservation model per resource per task.

    PAUSED Resource Policy:
    - PAUSED tasks retain their pre-existing resource reservations without progressing work.
    - Reservations are held until the task is resumed (ACTIVE), cancelled (CANCELLED), or failed (FAILED).

    Atomicity:
    - All operation methods (activate, process_round, change_status) validate all domain constraints
      before applying mutations. Any failure raises DomainRuleViolation and leaves the state unchanged.

    Idempotency:
    - Commands evaluated in process_round check (session_id, round_number, operation_id).
    - Replaying an already-processed command returns the stored result with idempotent_replay=True
      without duplicate state mutations, duplicate journal transitions, or double reservations.
    """

    @staticmethod
    def state_from_snapshots(
        session_id: str, snapshots: tuple[ResourceStateSnapshot, ...]
    ) -> TaskExecutionState:
        return TaskExecutionState(
            session_id=session_id,
            resources=tuple(ExecutionResourceState.from_snapshot(item) for item in snapshots),
        )

    @staticmethod
    def add_task(state: TaskExecutionState, task: TaskExecution) -> TaskExecutionState:
        if task.session_id != state.session_id:
            raise DomainRuleViolation("Task belongs to another session.")
        if any(item.id == task.id for item in state.tasks):
            raise DomainRuleViolation("Execution task already exists.")
        return replace(state, tasks=tuple(sorted((*state.tasks, task), key=lambda item: item.id)))

    @staticmethod
    def activate(
        state: TaskExecutionState,
        task_id: str,
        round_number: int,
        allocations: tuple[TaskResourceAllocation, ...],
    ) -> RoundExecutionResult:
        task = state.task(task_id)
        if task.status is not TaskExecutionStatus.PLANNED:
            raise DomainRuleViolation("Only planned tasks can be activated.")
        if round_number != state.current_round:
            raise DomainRuleViolation("Activation must use the current round.")
        resources = list(state.resources)
        reservations: list[ResourceReservation] = []
        requirements = {item.id: item for item in task.resource_requirements}
        if requirements and {item.requirement_id for item in allocations} != set(requirements):
            raise DomainRuleViolation("Activation allocations do not match task requirements.")
        for allocation in allocations:
            resource = next(
                (item for item in resources if item.resource_id == allocation.resource_id), None
            )
            if resource is None:
                raise DomainRuleViolation("Activation resource is unavailable.")
            requirement = requirements.get(allocation.requirement_id)
            if requirement is not None:
                if requirement.minimum_quantity is not None and allocation.quantity < decimal(requirement.minimum_quantity, "Minimum quantity"):
                    raise DomainRuleViolation("Allocation quantity is below the task requirement.")
                if requirement.minimum_capacity is not None and allocation.capacity < decimal(requirement.minimum_capacity, "Minimum capacity"):
                    raise DomainRuleViolation("Allocation capacity is below the task requirement.")
                if requirement.resource_ids and allocation.resource_id not in requirement.resource_ids:
                    raise DomainRuleViolation("Allocation resource does not match the task requirement.")
            reservation = ResourceReservation(
                allocation.resource_id,
                task.id,
                allocation.quantity,
                allocation.capacity,
            )
            updated_resource = resource.reserve(reservation)
            resources = [
                updated_resource if item.resource_id == resource.resource_id else item
                for item in resources
            ]
            reservations.append(reservation)
        updated_task = replace(
            task,
            allocations=allocations,
            status=TaskExecutionStatus.ACTIVE,
            start_round=round_number,
            last_processed_round=round_number - 1,
        )
        transition = _transition(
            state.session_id,
            round_number,
            task,
            updated_task,
            TransitionType.ACTIVATED,
            Decimal("0"),
            tuple(reservations),
            TransitionReason.EXPLICIT_COMMAND,
            len(state.transitions),
        )
        updated_state = replace(
            state,
            tasks=tuple(updated_task if item.id == task.id else item for item in state.tasks),
            resources=tuple(sorted(resources, key=lambda item: item.resource_id)),
            transitions=state.transitions + (transition,),
        )
        return RoundExecutionResult(updated_state, (transition,))

    @staticmethod
    def process_round(
        state: TaskExecutionState, command: RoundCommand
    ) -> RoundExecutionResult:
        """Apply one ordered round atomically; replaying its operation is idempotent."""
        if command.session_id != state.session_id:
            raise DomainRuleViolation("Round command belongs to another session.")
        for processed in state.processed_rounds:
            if (
                processed.session_id == command.session_id
                and processed.round_number == command.round_number
                and processed.operation_id == command.operation_id
            ):
                return RoundExecutionResult(state, processed.transitions, True)
        if command.round_number != state.current_round + 1:
            raise DomainRuleViolation("Round command is not the next expected round.")
        if any(item.round_number == command.round_number for item in state.processed_rounds):
            raise DomainRuleViolation("Round already processed with another operation.")

        tasks = list(state.tasks)
        resources = list(state.resources)
        transitions: list[ExecutionTransition] = []
        for task in sorted(state.tasks, key=lambda item: item.id):
            if task.status is not TaskExecutionStatus.ACTIVE:
                continue
            delta = min(task.productivity_per_round, task.remaining_work)
            if delta <= 0:
                raise DomainRuleViolation("Active task cannot progress with zero productivity.")
            completed = task.completed_work + delta
            new_status = (
                TaskExecutionStatus.COMPLETED
                if completed == task.planned_work
                else TaskExecutionStatus.ACTIVE
            )
            updated_task = replace(
                task,
                completed_work=completed,
                last_processed_round=command.round_number,
                status=new_status,
                completion_round=(
                    command.round_number if new_status is TaskExecutionStatus.COMPLETED else None
                ),
            )
            changes: list[ResourceReservation] = []
            if new_status is TaskExecutionStatus.COMPLETED:
                for allocation in task.allocations:
                    resource = next(
                        item for item in resources if item.resource_id == allocation.resource_id
                    )
                    resources = [
                        item for item in resources if item.resource_id != resource.resource_id
                    ]
                    resources.append(resource.release(task.id))
                    changes.append(
                        ResourceReservation(
                            allocation.resource_id,
                            task.id,
                            -allocation.quantity,
                            -allocation.capacity,
                        )
                    )
            transition = _transition(
                state.session_id,
                command.round_number,
                task,
                updated_task,
                (
                    TransitionType.COMPLETED
                    if new_status is TaskExecutionStatus.COMPLETED
                    else TransitionType.PROGRESSED
                ),
                delta,
                tuple(changes),
                (
                    TransitionReason.WORK_COMPLETE
                    if new_status is TaskExecutionStatus.COMPLETED
                    else TransitionReason.ROUND_PROGRESS
                ),
                len(state.transitions) + len(transitions),
            )
            tasks[next(i for i, item in enumerate(tasks) if item.id == task.id)] = updated_task
            transitions.append(transition)

        processed = ProcessedRound(
            command.session_id,
            command.round_number,
            command.operation_id,
            tuple(transitions),
        )
        return RoundExecutionResult(
            replace(
                state,
                current_round=command.round_number,
                tasks=tuple(sorted(tasks, key=lambda item: item.id)),
                resources=tuple(sorted(resources, key=lambda item: item.resource_id)),
                transitions=state.transitions + tuple(transitions),
                processed_rounds=state.processed_rounds + (processed,),
            ),
            tuple(transitions),
        )

    @staticmethod
    def change_status(
        state: TaskExecutionState,
        task_id: str,
        status: TaskExecutionStatus,
        round_number: int,
    ) -> RoundExecutionResult:
        task = state.task(task_id)
        updated = task.transition(status, round_number)
        resources = list(state.resources)
        changes: list[ResourceReservation] = []
        if status in TERMINAL:
            for allocation in task.allocations:
                resource = next(
                    (item for item in resources if item.resource_id == allocation.resource_id),
                    None,
                )
                if resource is None:
                    raise DomainRuleViolation("Task reservation resource is unavailable.")
                resources = [
                    item for item in resources if item.resource_id != resource.resource_id
                ]
                resources.append(resource.release(task.id))
                changes.append(
                    ResourceReservation(
                        allocation.resource_id,
                        task.id,
                        -allocation.quantity,
                        -allocation.capacity,
                    )
                )
        transition = _transition(
            state.session_id,
            round_number,
            task,
            updated,
            {
                TaskExecutionStatus.PAUSED: TransitionType.PAUSED,
                TaskExecutionStatus.ACTIVE: TransitionType.RESUMED,
                TaskExecutionStatus.FAILED: TransitionType.FAILED,
                TaskExecutionStatus.CANCELLED: TransitionType.CANCELLED,
            }[status],
            Decimal("0"),
            tuple(changes),
            TransitionReason.RESOURCE_RELEASED if changes else TransitionReason.EXPLICIT_COMMAND,
            len(state.transitions),
        )
        return RoundExecutionResult(
            replace(
                state,
                tasks=tuple(updated if item.id == task.id else item for item in state.tasks),
                resources=tuple(sorted(resources, key=lambda item: item.resource_id)),
                transitions=state.transitions + (transition,),
            ),
            (transition,),
        )


def _transition(
    session_id: str,
    round_number: int,
    previous: TaskExecution,
    updated: TaskExecution,
    transition_type: TransitionType,
    progress_delta: Decimal,
    reservation_changes: tuple[ResourceReservation, ...],
    reason: TransitionReason,
    order: int,
) -> ExecutionTransition:
    transition_id = str(
        uuid5(
            NAMESPACE_URL,
            f"tps360:{session_id}:{round_number}:{previous.id}:{order}:{transition_type}",
        )
    )
    return ExecutionTransition(
        id=transition_id,
        session_id=session_id,
        round_number=round_number,
        task_id=previous.id,
        transition_type=transition_type,
        previous_status=previous.status,
        new_status=updated.status,
        progress_delta=progress_delta,
        reservation_changes=reservation_changes,
        reason=reason,
        order=order,
    )
















