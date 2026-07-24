from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Protocol
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation

from .enums import (
    ApprovalRule,
    DecisionPriority,
    DecisionRequestStatus,
    DecisionSubmissionStatus,
    DecisionType,
    EventRuntimeStatus,
    ScenarioRuntimeStatus,
    ScenarioValidationLevel,
    SimulationStatus,
)

if TYPE_CHECKING:
    from .event_scheduler import EventScheduler
    from .scenario_runtime import ScenarioRuntime

from .events import (
    DecisionApprovalRecorded,
    DecisionApproved,
    DecisionCancelled,
    DecisionExecuted,
    DecisionExpired,
    DecisionOutcomeCreated,
    DecisionRejected,
    DecisionRejectionRecorded,
    DecisionRequestCreated,
    DecisionRequestOpened,
    DecisionReviewStarted,
    DecisionSubmissionValidated,
    DecisionSubmissionWithdrawn,
    DecisionSubmitted,
)


@dataclass(frozen=True)
class DecisionOption:
    id: str
    label: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.label.strip():
            raise DomainRuleViolation("Decision options must have non-empty identifiers and labels.")


@dataclass(frozen=True)
class ResourceAllocation:
    resource_id: UUID
    quantity: float

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise DomainRuleViolation("Resource allocation cannot be negative.")


@dataclass(frozen=True)
class DecisionParticipationPolicy:
    """Immutable, infrastructure-free authorization and agreement contract."""

    permitted_team_ids: tuple[UUID, ...]
    permitted_role_ids: tuple[UUID, ...]
    approval_role_ids: tuple[UUID, ...] = ()
    approval_rule: ApprovalRule = ApprovalRule.ALL
    minimum_quorum: int = 0
    allow_multiple_active_submissions: bool = False

    def __post_init__(self) -> None:
        if self.minimum_quorum < 0:
            raise DomainRuleViolation("Decision quorum cannot be negative.")
        for values, label in (
            (self.permitted_team_ids, "Permitted team IDs"),
            (self.permitted_role_ids, "Permitted role IDs"),
            (self.approval_role_ids, "Approval role IDs"),
        ):
            if len(values) != len(set(values)):
                raise DomainRuleViolation(f"{label} must not contain duplicates.")
        if self.minimum_quorum > len(self.permitted_team_ids):
            raise DomainRuleViolation("Decision quorum cannot exceed permitted teams.")

    def can_view(self, role_id: UUID) -> bool:
        return role_id in self.permitted_role_ids

    def can_submit(self, team_id: UUID, role_id: UUID) -> bool:
        return team_id in self.permitted_team_ids and self.can_view(role_id)


@dataclass(frozen=True)
class DecisionRequest:
    id: UUID
    simulation_id: UUID
    scenario_id: UUID
    related_event_id: UUID | None
    name: str
    description: str
    decision_type: DecisionType
    priority: DecisionPriority
    created_at: datetime
    deadline: datetime
    allowed_role_ids: tuple[UUID, ...]
    options: tuple[DecisionOption, ...]
    allow_free_text: bool
    justification_required: bool
    participation_policy: DecisionParticipationPolicy
    resource_limits: tuple[ResourceAllocation, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.description.strip():
            raise DomainRuleViolation("Decision request name and description must not be empty.")
        if self.deadline < self.created_at:
            raise DomainRuleViolation("Decision deadline cannot precede creation time.")
        if self.version < 1:
            raise DomainRuleViolation("Decision request version must be at least one.")
        if not self.allowed_role_ids or len(self.allowed_role_ids) != len(set(self.allowed_role_ids)):
            raise DomainRuleViolation("Decision request roles must be non-empty and unique.")
        if set(self.allowed_role_ids) != set(self.participation_policy.permitted_role_ids):
            raise DomainRuleViolation("Decision request roles must match its participation policy.")
        if len({option.id for option in self.options}) != len(self.options):
            raise DomainRuleViolation("Decision option IDs must be unique.")
        if self.decision_type in {DecisionType.SINGLE_CHOICE, DecisionType.MULTIPLE_CHOICE, DecisionType.PRIORITIZATION} and not self.options:
            raise DomainRuleViolation("This decision type requires options.")
        if len({allocation.resource_id for allocation in self.resource_limits}) != len(self.resource_limits):
            raise DomainRuleViolation("Decision resource limits must be unique.")
        if len({key for key, _ in self.metadata}) != len(self.metadata) or any(not key.strip() for key, _ in self.metadata):
            raise DomainRuleViolation("Decision metadata keys must be non-empty and unique.")

    def resource_limit_for(self, resource_id: UUID) -> float | None:
        return next((item.quantity for item in self.resource_limits if item.resource_id == resource_id), None)


@dataclass
class DecisionSubmission:
    id: UUID
    request_id: UUID
    team_id: UUID
    role_id: UUID
    selected_option_ids: tuple[str, ...]
    justification: str
    resource_allocations: tuple[ResourceAllocation, ...]
    confidence: int | None
    submitted_at: datetime
    version: int = 1
    status: DecisionSubmissionStatus = DecisionSubmissionStatus.SUBMITTED

    def __post_init__(self) -> None:
        if self.version < 1:
            raise DomainRuleViolation("Decision submission version must be at least one.")
        if self.confidence is not None and not 0 <= self.confidence <= 100:
            raise DomainRuleViolation("Decision confidence must be between zero and 100.")
        if len(self.selected_option_ids) != len(set(self.selected_option_ids)):
            raise DomainRuleViolation("Selected decision options must not contain duplicates.")
        if len({item.resource_id for item in self.resource_allocations}) != len(self.resource_allocations):
            raise DomainRuleViolation("Submission resource allocations must be unique.")

    def __setattr__(self, name: str, value: object) -> None:
        if hasattr(self, "status") and self.status in {DecisionSubmissionStatus.WITHDRAWN, DecisionSubmissionStatus.ACCEPTED, DecisionSubmissionStatus.DECLINED} and name in {"status", "selected_option_ids", "justification", "resource_allocations", "confidence"}:
            raise DomainRuleViolation("Final decision submissions cannot be changed.")
        super().__setattr__(name, value)


@dataclass(frozen=True)
class DecisionApproval:
    role_id: UUID
    approved: bool
    reason: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise DomainRuleViolation("Decision approval reason must not be empty.")


@dataclass(frozen=True)
class DecisionReadiness:
    messages: tuple[tuple[ScenarioValidationLevel, str, str], ...]
    missing_approvals: tuple[UUID, ...]
    quorum_state: tuple[int, int]

    @property
    def errors(self) -> tuple[tuple[ScenarioValidationLevel, str, str], ...]:
        return tuple(message for message in self.messages if message[0] is ScenarioValidationLevel.ERROR)

    @property
    def warnings(self) -> tuple[tuple[ScenarioValidationLevel, str, str], ...]:
        return tuple(message for message in self.messages if message[0] is ScenarioValidationLevel.WARNING)

    @property
    def information(self) -> tuple[tuple[ScenarioValidationLevel, str, str], ...]:
        return tuple(message for message in self.messages if message[0] is ScenarioValidationLevel.INFORMATION)

    @property
    def ready(self) -> bool:
        return not self.errors and not self.missing_approvals and self.quorum_state[0] >= self.quorum_state[1]


@dataclass(frozen=True)
class DecisionOutcome:
    request_id: UUID
    accepted_option_ids: tuple[str, ...]
    submission_ids: tuple[UUID, ...]
    approvals: tuple[DecisionApproval, ...]
    rationale: str
    resource_allocations: tuple[ResourceAllocation, ...]
    approved_at: datetime
    version: int
    correlation_id: UUID
    causation_id: UUID | None

    def __post_init__(self) -> None:
        if not self.rationale.strip() or self.version < 1:
            raise DomainRuleViolation("Decision outcome must have rationale and a valid version.")


class DecisionSimulation(Protocol):
    id: UUID
    status: SimulationStatus
    current_time: datetime

    @property
    def scenario_runtime(self) -> ScenarioRuntime | None: ...

    @property
    def event_scheduler(self) -> EventScheduler | None: ...


@dataclass
class DecisionRuntime:
    request: DecisionRequest
    status: DecisionRequestStatus = DecisionRequestStatus.DRAFT
    submissions: tuple[DecisionSubmission, ...] = ()
    approvals: tuple[DecisionApproval, ...] = ()
    outcome: DecisionOutcome | None = None
    audit_trail: tuple[object, ...] = field(default_factory=tuple)

    def __setattr__(self, name: str, value: object) -> None:
        if hasattr(self, "status") and self.status in {DecisionRequestStatus.EXECUTED, DecisionRequestStatus.EXPIRED, DecisionRequestStatus.CANCELLED} and name in {"status", "submissions", "approvals", "outcome", "audit_trail"}:
            raise DomainRuleViolation("Final decision runtimes cannot be changed.")
        super().__setattr__(name, value)


@dataclass
class DecisionEngine:
    simulation_id: UUID
    scenario_id: UUID
    runtimes: tuple[DecisionRuntime, ...] = ()
    audit_trail: tuple[object, ...] = field(default_factory=tuple)

    def create(self, simulation: DecisionSimulation, request: DecisionRequest) -> DecisionRuntime:
        self._ensure_running(simulation)
        if request.simulation_id != self.simulation_id or request.scenario_id != self.scenario_id or request.simulation_id != simulation.id:
            raise DomainRuleViolation("Decision request does not belong to this simulation and scenario.")
        if request.related_event_id is not None:
            scheduler = simulation.event_scheduler
            if scheduler is None or not any(runtime.definition.id == request.related_event_id and runtime.status is EventRuntimeStatus.ACTIVE for runtime in scheduler.event_runtimes):
                raise DomainRuleViolation("Related decision event must be active in this simulation.")
        if any(runtime.request.id == request.id for runtime in self.runtimes):
            raise DomainRuleViolation("Decision request ID already exists.")
        runtime = DecisionRuntime(request)
        self.runtimes = (*self.runtimes, runtime)
        self._record(runtime, DecisionRequestCreated(self.simulation_id, self.scenario_id, request.id, request.version, simulation.current_time, "created"))
        return runtime

    def open(self, request_id: UUID, occurred_at: datetime) -> None:
        runtime = self._runtime(request_id)
        self._ensure(runtime, {DecisionRequestStatus.DRAFT}, "Only draft decisions can be opened.")
        self._transition(runtime, DecisionRequestStatus.OPEN, occurred_at, "opened")

    def submit(self, simulation: DecisionSimulation, submission: DecisionSubmission) -> None:
        self._ensure_running(simulation)
        runtime = self._runtime(submission.request_id)
        if simulation.current_time > runtime.request.deadline:
            self._expire(runtime, simulation.current_time)
        self._ensure(runtime, {DecisionRequestStatus.OPEN}, "Submissions require an open decision request.")
        request = runtime.request
        if submission.submitted_at > request.deadline or simulation.current_time > request.deadline:
            raise DomainRuleViolation("Decision submissions are not allowed after the deadline.")
        if not request.participation_policy.can_submit(submission.team_id, submission.role_id):
            raise DomainRuleViolation("Decision team or role is not permitted to submit.")
        if not request.participation_policy.allow_multiple_active_submissions and any(item.team_id == submission.team_id and item.status not in {DecisionSubmissionStatus.WITHDRAWN, DecisionSubmissionStatus.DECLINED} for item in runtime.submissions):
            raise DomainRuleViolation("Team already has an active submission for this decision.")
        self._validate_submission(request, submission)
        submission.status = DecisionSubmissionStatus.VALID
        runtime.submissions = (*runtime.submissions, submission)
        self._record(runtime, DecisionSubmitted(self.simulation_id, self.scenario_id, request.id, request.version, simulation.current_time, "submitted", submission.id))
        self._record(runtime, DecisionSubmissionValidated(self.simulation_id, self.scenario_id, request.id, request.version, simulation.current_time, "valid", submission.id))

    def withdraw(self, request_id: UUID, submission_id: UUID, occurred_at: datetime) -> None:
        runtime = self._runtime(request_id)
        self._ensure(runtime, {DecisionRequestStatus.OPEN}, "Submissions can only be withdrawn before review.")
        submission = self._submission(runtime, submission_id)
        if submission.status is not DecisionSubmissionStatus.VALID:
            raise DomainRuleViolation("Only valid submissions can be withdrawn.")
        submission.status = DecisionSubmissionStatus.WITHDRAWN
        self._record(runtime, DecisionSubmissionWithdrawn(self.simulation_id, self.scenario_id, request_id, runtime.request.version, occurred_at, "withdrawn", submission_id))

    def start_review(self, request_id: UUID, occurred_at: datetime) -> None:
        runtime = self._runtime(request_id)
        self._ensure(runtime, {DecisionRequestStatus.OPEN}, "Only open decisions can enter review.")
        self._transition(runtime, DecisionRequestStatus.UNDER_REVIEW, occurred_at, "review_started")
        self._record(runtime, DecisionReviewStarted(self.simulation_id, self.scenario_id, request_id, runtime.request.version, occurred_at, "review_started"))

    def record_approval(self, request_id: UUID, approval: DecisionApproval) -> DecisionReadiness:
        runtime = self._runtime(request_id)
        self._ensure(runtime, {DecisionRequestStatus.OPEN, DecisionRequestStatus.UNDER_REVIEW}, "Decision approval requires an open or reviewed request.")
        if approval.role_id not in runtime.request.participation_policy.approval_role_ids:
            raise DomainRuleViolation("Role is not an approval role for this decision.")
        if any(item.role_id == approval.role_id for item in runtime.approvals):
            raise DomainRuleViolation("An approval role cannot vote twice.")
        runtime.approvals = (*runtime.approvals, approval)
        event_type = DecisionApprovalRecorded if approval.approved else DecisionRejectionRecorded
        self._record(runtime, event_type(self.simulation_id, self.scenario_id, request_id, runtime.request.version, approval.recorded_at, approval.reason, approval.role_id))
        return self.readiness(request_id)

    def readiness(self, request_id: UUID) -> DecisionReadiness:
        runtime = self._runtime(request_id)
        policy = runtime.request.participation_policy
        approved_roles = {item.role_id for item in runtime.approvals if item.approved}
        rejected = any(not item.approved for item in runtime.approvals)
        missing = tuple(role for role in policy.approval_role_ids if role not in approved_roles)
        active_teams = {item.team_id for item in runtime.submissions if item.status is DecisionSubmissionStatus.VALID}
        messages: list[tuple[ScenarioValidationLevel, str, str]] = [(ScenarioValidationLevel.INFORMATION, "readiness_checked", "Decision readiness was evaluated deterministically.")]
        if rejected:
            messages.append((ScenarioValidationLevel.ERROR, "approval_rejected", "An approval role rejected the decision."))
        if policy.approval_rule is ApprovalRule.ANY and approved_roles:
            missing = ()
        elif policy.approval_rule is ApprovalRule.ANY and policy.approval_role_ids:
            messages.append((ScenarioValidationLevel.ERROR, "missing_approval", "At least one approval is required."))
        elif missing:
            messages.append((ScenarioValidationLevel.ERROR, "missing_approvals", "Required approvals are missing."))
        if len(active_teams) < policy.minimum_quorum:
            messages.append((ScenarioValidationLevel.ERROR, "quorum_not_met", "Team quorum is not met."))
        options_by_team = {item.team_id: item.selected_option_ids for item in runtime.submissions if item.status is DecisionSubmissionStatus.VALID}
        if len(set(options_by_team.values())) > 1 and runtime.request.decision_type in {DecisionType.COORDINATED, DecisionType.APPROVAL}:
            messages.append((ScenarioValidationLevel.WARNING, "conflicting_submissions", "Active submissions contain different choices."))
        return DecisionReadiness(tuple(messages), missing, (len(active_teams), policy.minimum_quorum))

    def approve(self, request_id: UUID, occurred_at: datetime, rationale: str, correlation_id: UUID, causation_id: UUID | None = None) -> DecisionOutcome:
        runtime = self._runtime(request_id)
        self._ensure(runtime, {DecisionRequestStatus.OPEN, DecisionRequestStatus.UNDER_REVIEW}, "Only open or reviewed decisions can be approved.")
        readiness = self.readiness(request_id)
        if not readiness.ready:
            raise DomainRuleViolation("Decision is not ready for approval.")
        submissions = tuple(item for item in runtime.submissions if item.status is DecisionSubmissionStatus.VALID)
        accepted_options = tuple(sorted({option for item in submissions for option in item.selected_option_ids}))
        allocations = tuple(sorted((allocation for item in submissions for allocation in item.resource_allocations), key=lambda item: str(item.resource_id)))
        outcome = DecisionOutcome(request_id, accepted_options, tuple(item.id for item in submissions), runtime.approvals, rationale, allocations, occurred_at, runtime.request.version, correlation_id, causation_id)
        runtime.outcome = outcome
        self._record(runtime, DecisionApproved(self.simulation_id, self.scenario_id, request_id, runtime.request.version, occurred_at, "approved"))
        self._record(runtime, DecisionOutcomeCreated(self.simulation_id, self.scenario_id, request_id, runtime.request.version, occurred_at, "outcome_created", correlation_id, causation_id))
        runtime.status = DecisionRequestStatus.APPROVED
        return outcome

    def reject(self, request_id: UUID, occurred_at: datetime, reason: str) -> None:
        runtime = self._runtime(request_id)
        self._ensure(runtime, {DecisionRequestStatus.OPEN, DecisionRequestStatus.UNDER_REVIEW}, "Only open or reviewed decisions can be rejected.")
        self._record(runtime, DecisionRejected(self.simulation_id, self.scenario_id, request_id, runtime.request.version, occurred_at, reason))
        runtime.status = DecisionRequestStatus.REJECTED

    def execute(self, request_id: UUID, occurred_at: datetime) -> None:
        runtime = self._runtime(request_id)
        self._ensure(runtime, {DecisionRequestStatus.APPROVED}, "Only approved decisions can be executed.")
        self._record(runtime, DecisionExecuted(self.simulation_id, self.scenario_id, request_id, runtime.request.version, occurred_at, "executed"))
        runtime.status = DecisionRequestStatus.EXECUTED

    def expire(self, request_id: UUID, occurred_at: datetime) -> None:
        runtime = self._runtime(request_id)
        self._expire(runtime, occurred_at)

    def cancel(self, request_id: UUID, occurred_at: datetime) -> None:
        runtime = self._runtime(request_id)
        if runtime.status in {DecisionRequestStatus.EXECUTED, DecisionRequestStatus.EXPIRED, DecisionRequestStatus.CANCELLED}:
            raise DomainRuleViolation("Final decisions cannot be cancelled.")
        self._record(runtime, DecisionCancelled(self.simulation_id, self.scenario_id, request_id, runtime.request.version, occurred_at, "cancelled"))
        runtime.status = DecisionRequestStatus.CANCELLED

    def _validate_submission(self, request: DecisionRequest, submission: DecisionSubmission) -> None:
        selected = set(submission.selected_option_ids)
        allowed = {option.id for option in request.options}
        if not selected <= allowed:
            raise DomainRuleViolation("Submission contains options not allowed by the decision request.")
        if request.justification_required and not submission.justification.strip():
            raise DomainRuleViolation("Decision justification is required.")
        if request.decision_type is DecisionType.SINGLE_CHOICE and len(selected) != 1:
            raise DomainRuleViolation("Single-choice decisions require exactly one option.")
        if request.decision_type is DecisionType.MULTIPLE_CHOICE and not selected:
            raise DomainRuleViolation("Multiple-choice decisions require at least one option.")
        if request.decision_type is DecisionType.FREE_TEXT and not request.allow_free_text:
            raise DomainRuleViolation("Free-text response is not allowed.")
        if request.decision_type is DecisionType.RESOURCE_ALLOCATION and not submission.resource_allocations:
            raise DomainRuleViolation("Resource allocation decisions require allocations.")
        for allocation in submission.resource_allocations:
            limit = request.resource_limit_for(allocation.resource_id)
            if limit is None or allocation.quantity > limit:
                raise DomainRuleViolation("Submission resource allocation exceeds the available limit.")

    def _expire(self, runtime: DecisionRuntime, occurred_at: datetime) -> None:
        if occurred_at <= runtime.request.deadline:
            raise DomainRuleViolation("Decision cannot expire before its deadline.")
        self._ensure(runtime, {DecisionRequestStatus.OPEN, DecisionRequestStatus.UNDER_REVIEW}, "Only unfinished decisions can expire.")
        self._record(runtime, DecisionExpired(self.simulation_id, self.scenario_id, runtime.request.id, runtime.request.version, occurred_at, "deadline_expired"))
        runtime.status = DecisionRequestStatus.EXPIRED

    def _transition(self, runtime: DecisionRuntime, status: DecisionRequestStatus, occurred_at: datetime, reason: str) -> None:
        event = DecisionRequestOpened(self.simulation_id, self.scenario_id, runtime.request.id, runtime.request.version, occurred_at, reason)
        self._record(runtime, event)
        runtime.status = status

    def _ensure_running(self, simulation: DecisionSimulation) -> None:
        if simulation.status is not SimulationStatus.RUNNING:
            raise DomainRuleViolation("Decision engine runs only in running simulations.")
        scenario = simulation.scenario_runtime
        if scenario is None or scenario.status is not ScenarioRuntimeStatus.ACTIVE:
            raise DomainRuleViolation("Decision engine requires an active scenario runtime.")

    @staticmethod
    def _ensure(runtime: DecisionRuntime, expected: set[DecisionRequestStatus], message: str) -> None:
        if runtime.status not in expected:
            raise DomainRuleViolation(message)

    def _runtime(self, request_id: UUID) -> DecisionRuntime:
        for runtime in self.runtimes:
            if runtime.request.id == request_id:
                return runtime
        raise DomainRuleViolation("Decision request runtime is unavailable.")

    @staticmethod
    def _submission(runtime: DecisionRuntime, submission_id: UUID) -> DecisionSubmission:
        for submission in runtime.submissions:
            if submission.id == submission_id:
                return submission
        raise DomainRuleViolation("Decision submission is unavailable.")

    def _record(self, runtime: DecisionRuntime, event: object) -> None:
        runtime.audit_trail = (*runtime.audit_trail, event)
        self.audit_trail = (*self.audit_trail, event)