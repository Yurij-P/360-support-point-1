from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

from tps360.core.exceptions import DomainRuleViolation


class InteractionType(StrEnum):
    REPORT = "REPORT"
    NOTIFY = "NOTIFY"
    REQUEST = "REQUEST"
    COORDINATE = "COORDINATE"
    ASSIGN = "ASSIGN"
    ORDER = "ORDER"
    ESCALATE = "ESCALATE"


class RelationshipDirection(StrEnum):
    DIRECTED = "directed"
    BIDIRECTIONAL = "bidirectional"


class ResourceAccessMode(StrEnum):
    DIRECT = "DIRECT"
    REQUEST_REQUIRED = "REQUEST_REQUIRED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    ASSIGNMENT_REQUIRED = "ASSIGNMENT_REQUIRED"
    ORDER_REQUIRED = "ORDER_REQUIRED"
    NO_ACCESS = "NO_ACCESS"


class ResourceAvailability(StrEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    DAMAGED = "damaged"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ResourceRenewalPolicy(StrEnum):
    NON_RENEWABLE = "non_renewable"
    RENEWABLE = "renewable"
    CONSUMABLE = "consumable"
    SCENARIO_DEFINED = "scenario_defined"


class ConsumptionTiming(StrEnum):
    ON_START = "on_start"
    PER_ROUND = "per_round"
    ON_COMPLETION = "on_completion"
    SCENARIO_DEFINED = "scenario_defined"


class DurationCalculationStrategy(StrEnum):
    WORK_OVER_PRODUCTIVITY = "work_over_productivity"
    FIXED_DURATION = "fixed_duration"
    SCENARIO_DEFINED = "scenario_defined"


class DurationRoundingMode(StrEnum):
    CEIL = "ceil"
    FLOOR = "floor"
    ROUND = "round"
    SCENARIO_DEFINED = "scenario_defined"


class DurationEstimateStatus(StrEnum):
    ESTIMABLE = "estimable"
    BLOCKED = "blocked"
    INDETERMINATE = "indeterminate"
    INSUFFICIENT_DATA = "insufficient_data"


class RequirementKind(StrEnum):
    CAPABILITY = "capability"
    AUTHORITY = "authority"
    ACTION_PERMISSION = "action_permission"
    INTERACTION_PERMISSION = "interaction_permission"
    RELATIONSHIP = "relationship"
    RESOURCE_ACCESS = "resource_access"
    RESOURCE_TYPE = "resource_type"
    RESOURCE_PROPERTY = "resource_property"
    RESOURCE_AVAILABILITY = "resource_availability"
    PREREQUISITE = "prerequisite"


class RequirementCriticality(StrEnum):
    CRITICAL = "critical"
    NON_CRITICAL = "non_critical"


class PrerequisiteStatus(StrEnum):
    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    UNKNOWN = "unknown"
    MISSING = "missing"


class CompatibilityOutcome(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    DEGRADED = "DEGRADED"
    PARTIAL = "PARTIAL"
    INDETERMINATE = "INDETERMINATE"


class CompatibilityReasonCode(StrEnum):
    ACTION_NOT_PERMITTED = "ACTION_NOT_PERMITTED"
    MISSING_CAPABILITY = "MISSING_CAPABILITY"
    MISSING_AUTHORITY = "MISSING_AUTHORITY"
    INTERACTION_NOT_PERMITTED = "INTERACTION_NOT_PERMITTED"
    INVALID_RELATIONSHIP = "INVALID_RELATIONSHIP"
    INVALID_RELATIONSHIP_DIRECTION = "INVALID_RELATIONSHIP_DIRECTION"
    RESOURCE_ACCESS_DENIED = "RESOURCE_ACCESS_DENIED"
    RESOURCE_ACCESS_REQUIREMENT_UNMET = "RESOURCE_ACCESS_REQUIREMENT_UNMET"
    RESOURCE_MISMATCH = "RESOURCE_MISMATCH"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
    INSUFFICIENT_RESOURCE_CAPACITY = "INSUFFICIENT_RESOURCE_CAPACITY"
    RESOURCE_ALREADY_COMMITTED = "RESOURCE_ALREADY_COMMITTED"
    PREREQUISITE_UNMET = "PREREQUISITE_UNMET"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class ActorProfile:
    id: str
    capabilities: tuple[str, ...] = ()
    authorities: tuple[str, ...] = ()
    organization_id: str | None = None
    unit_id: str | None = None
    attributes: Mapping[str, object] | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Requirement:
    id: str
    kind: RequirementKind
    expected: object
    criticality: RequirementCriticality = RequirementCriticality.CRITICAL
    scope: str | None = None
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class DurationCalculationPolicy:
    id: str
    strategy: DurationCalculationStrategy
    work_unit: str
    productivity_unit: str
    time_unit: str = "round"
    rounding: DurationRoundingMode = DurationRoundingMode.CEIL
    minimum_effective_productivity: float | None = None
    maximum_effective_productivity: float | None = None
    allow_zero_productivity_result: bool = False
    supports_diminishing_returns: bool = False
    supports_dependency: bool = False
    supports_synergy: bool = False
    modifier_keys: tuple[str, ...] = ()
    blocked_status: DurationEstimateStatus = DurationEstimateStatus.BLOCKED
    insufficient_data_status: DurationEstimateStatus = DurationEstimateStatus.INSUFFICIENT_DATA
    attributes: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "Duration policy id")
        _require_non_empty(self.work_unit, "Duration policy work unit")
        _require_non_empty(self.productivity_unit, "Duration policy productivity unit")
        _require_non_empty(self.time_unit, "Duration policy time unit")
        _require_unique(self.modifier_keys, "Duration policy modifier keys")
        _require_non_negative_optional(
            self.minimum_effective_productivity, "Minimum effective productivity"
        )
        _require_non_negative_optional(
            self.maximum_effective_productivity, "Maximum effective productivity"
        )
        if (
            self.minimum_effective_productivity is not None
            and self.maximum_effective_productivity is not None
            and self.minimum_effective_productivity > self.maximum_effective_productivity
        ):
            raise DomainRuleViolation(
                "Duration policy minimum productivity cannot exceed maximum productivity."
            )
        if (
            self.strategy is DurationCalculationStrategy.WORK_OVER_PRODUCTIVITY
            and self.rounding is DurationRoundingMode.SCENARIO_DEFINED
        ):
            raise DomainRuleViolation(
                "Work-over-productivity duration policy requires explicit rounding."
            )


@dataclass(frozen=True)
class ResourceCommitmentRequirement:
    id: str
    resource_type: str | None = None
    resource_ids: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    required_properties: Mapping[str, object] | None = None
    minimum_quantity: float | None = None
    target_quantity: float | None = None
    maximum_quantity: float | None = None
    minimum_capacity: float | None = None
    target_capacity: float | None = None
    productivity_units: float | None = None
    blocks_resource: bool = True
    partial_execution_allowed: bool = False
    parallel_use_allowed: bool = False
    additional_resources_reduce_duration: bool = False
    insufficient_resources_degrade_progress: bool = False
    can_pause: bool = False
    can_reallocate: bool = False
    can_reinforce: bool = False
    consumption_timing: ConsumptionTiming | None = None
    release_conditions: tuple[str, ...] = ()
    criticality: RequirementCriticality = RequirementCriticality.CRITICAL
    attributes: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "Resource commitment requirement id")
        _require_unique(self.resource_ids, "Resource commitment resource ids")
        _require_unique(self.required_capabilities, "Resource commitment capabilities")
        _require_non_negative_optional(self.minimum_quantity, "Minimum quantity")
        _require_non_negative_optional(self.target_quantity, "Target quantity")
        _require_non_negative_optional(self.maximum_quantity, "Maximum quantity")
        _require_non_negative_optional(self.minimum_capacity, "Minimum capacity")
        _require_non_negative_optional(self.target_capacity, "Target capacity")
        _require_non_negative_optional(self.productivity_units, "Productivity units")
        _require_ordered_bounds(
            self.minimum_quantity, self.target_quantity, self.maximum_quantity, "quantity"
        )
        _require_ordered_bounds(
            self.minimum_capacity, self.target_capacity, None, "capacity"
        )
        _require_unique(self.release_conditions, "Release conditions")


@dataclass(frozen=True)
class ActionWorkProfile:
    required_work_units: float | None = None
    fixed_duration_rounds: int | None = None
    duration_policy_id: str | None = None
    resource_commitments: tuple[ResourceCommitmentRequirement, ...] = ()
    contextual_modifiers: Mapping[str, object] | None = None
    attributes: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        _require_non_negative_optional(self.required_work_units, "Required work units")
        _require_non_negative_optional(self.fixed_duration_rounds, "Fixed duration rounds")
        if self.duration_policy_id is not None:
            _require_non_empty(self.duration_policy_id, "Duration policy reference")
        _require_unique(
            tuple(requirement.id for requirement in self.resource_commitments),
            "Action work resource commitment ids",
        )


@dataclass(frozen=True)
class ActionDefinition:
    id: str
    action_type: str
    required_capabilities: tuple[str, ...] = ()
    required_execution_authorities: tuple[str, ...] = ()
    required_initiation_authorities: tuple[str, ...] = ()
    permitted_interaction_types: tuple[InteractionType, ...] = ()
    resource_requirements: tuple[ResourceCommitmentRequirement, ...] = ()
    prerequisites: tuple[Requirement, ...] = ()
    work_profile: ActionWorkProfile | None = None
    visible_to_actor_ids: tuple[str, ...] = ()
    executable_by_actor_ids: tuple[str, ...] = ()
    attributes: Mapping[str, object] | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "Action definition id")
        _require_non_empty(self.action_type, "Action type")
        _require_unique(self.required_capabilities, "Action required capabilities")
        _require_unique(
            self.required_execution_authorities, "Action required execution authorities"
        )
        _require_unique(
            self.required_initiation_authorities, "Action required initiation authorities"
        )
        _require_unique(
            tuple(requirement.id for requirement in self.resource_requirements),
            "Action resource requirement ids",
        )
        _require_unique(
            tuple(requirement.id for requirement in self.prerequisites),
            "Action prerequisite ids",
        )


@dataclass(frozen=True)
class Relationship:
    source_id: str
    target_id: str
    relationship_type: str
    allowed_interaction_types: tuple[InteractionType, ...]
    direction: RelationshipDirection = RelationshipDirection.DIRECTED
    scope: str | None = None
    constraints: Mapping[str, object] | None = None
    state: str | None = None

    def allows(self, initiator_id: str, recipient_id: str, interaction_type: InteractionType) -> bool:
        return self.connects(initiator_id, recipient_id) and interaction_type in self.allowed_interaction_types

    def connects(self, initiator_id: str, recipient_id: str) -> bool:
        if self.source_id == initiator_id and self.target_id == recipient_id:
            return True
        return (
            self.direction is RelationshipDirection.BIDIRECTIONAL
            and self.source_id == recipient_id
            and self.target_id == initiator_id
        )

    def connects_reverse(self, initiator_id: str, recipient_id: str) -> bool:
        return self.source_id == recipient_id and self.target_id == initiator_id


@dataclass(frozen=True)
class InteractionIntent:
    initiator_id: str
    recipient_id: str
    interaction_type: InteractionType
    action_id: str | None = None
    action_type: str | None = None
    context: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ResourceProfile:
    id: str
    resource_type: str
    capabilities: tuple[str, ...] = ()
    properties: Mapping[str, object] | None = None
    availability: ResourceAvailability = ResourceAvailability.UNKNOWN
    quantity: float | None = None
    capacity: float | None = None
    renewal_policy: ResourceRenewalPolicy | None = None
    location: str | None = None
    state: str | None = None
    owner_id: str | None = None
    constraints: Mapping[str, object] | None = None
    attributes: Mapping[str, object] | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "Resource id")
        _require_non_empty(self.resource_type, "Resource type")
        _require_unique(self.capabilities, "Resource capabilities")
        _require_non_negative_optional(self.quantity, "Resource quantity")
        _require_non_negative_optional(self.capacity, "Resource capacity")


@dataclass(frozen=True)
class ResourceStateSnapshot:
    resource_id: str
    round_marker: int | str | None = None
    current_quantity: float | None = None
    available_quantity: float | None = None
    committed_quantity: float | None = None
    current_capacity: float | None = None
    available_capacity: float | None = None
    committed_capacity: float | None = None
    availability: ResourceAvailability = ResourceAvailability.UNKNOWN
    active_commitment_refs: tuple[str, ...] = ()
    attributes: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.resource_id, "Resource snapshot resource id")
        _require_non_negative_optional(self.current_quantity, "Current quantity")
        _require_non_negative_optional(self.available_quantity, "Available quantity")
        _require_non_negative_optional(self.committed_quantity, "Committed quantity")
        _require_non_negative_optional(self.current_capacity, "Current capacity")
        _require_non_negative_optional(self.available_capacity, "Available capacity")
        _require_non_negative_optional(self.committed_capacity, "Committed capacity")
        if (
            self.current_quantity is not None
            and self.available_quantity is not None
            and self.available_quantity > self.current_quantity
        ):
            raise DomainRuleViolation("Available quantity cannot exceed current quantity.")
        if (
            self.current_capacity is not None
            and self.available_capacity is not None
            and self.available_capacity > self.current_capacity
        ):
            raise DomainRuleViolation("Available capacity cannot exceed current capacity.")
        _require_unique(self.active_commitment_refs, "Active commitment references")


@dataclass(frozen=True)
class ResourceAccessGrant:
    actor_id: str
    resource_id: str | None = None
    resource_type: str | None = None
    access_mode: ResourceAccessMode = ResourceAccessMode.NO_ACCESS
    allowed_action_ids: tuple[str, ...] = ()
    scope: str | None = None
    required_authority: str | None = None
    required_interaction_type: InteractionType | None = None
    constraints: Mapping[str, object] | None = None
    state: str | None = None

    def covers(self, resource: ResourceProfile, action_id: str) -> bool:
        if self.resource_id is not None and self.resource_id != resource.id:
            return False
        if self.resource_type is not None and self.resource_type != resource.resource_type:
            return False
        return not self.allowed_action_ids or action_id in self.allowed_action_ids


@dataclass(frozen=True)
class TaskDemand:
    id: str
    action_definition_id: str
    required_work_units: float | None = None
    remaining_work_units: float | None = None
    duration_policy_id: str | None = None
    priority: str | None = None
    criticality: RequirementCriticality | None = None
    deadline: str | None = None
    time_window: str | None = None
    contextual_modifiers: Mapping[str, object] | None = None
    resource_requirement_overrides: tuple[ResourceCommitmentRequirement, ...] = ()
    state: str | None = None
    attributes: Mapping[str, object] | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "Task demand id")
        _require_non_empty(self.action_definition_id, "Task demand action definition id")
        if self.duration_policy_id is not None:
            _require_non_empty(self.duration_policy_id, "Task demand duration policy id")
        _require_non_negative_optional(self.required_work_units, "Task required work units")
        _require_non_negative_optional(self.remaining_work_units, "Task remaining work units")
        _require_unique(
            tuple(requirement.id for requirement in self.resource_requirement_overrides),
            "Task resource requirement override ids",
        )


@dataclass(frozen=True)
class ParticipantContext:
    participant_id: str
    actor_id: str
    session_id: str | None = None
    capabilities: tuple[str, ...] = ()
    authorities: tuple[str, ...] = ()
    self_executable_action_ids: tuple[str, ...] = ()
    permitted_interaction_types: tuple[InteractionType, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    resource_access_grants: tuple[ResourceAccessGrant, ...] = ()
    attributes: Mapping[str, object] | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkspaceResourceReference:
    resource_id: str | None
    resource_type: str | None
    access_mode: ResourceAccessMode
    allowed_action_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkspaceInteractionReference:
    recipient_id: str
    interaction_types: tuple[InteractionType, ...]
    relationship_type: str


@dataclass(frozen=True)
class ParticipantWorkspaceProjection:
    participant_id: str
    actor_id: str
    capabilities: tuple[str, ...]
    authorities: tuple[str, ...]
    self_executable_action_ids: tuple[str, ...]
    permitted_interaction_types: tuple[InteractionType, ...]
    interactions: tuple[WorkspaceInteractionReference, ...]
    resources: tuple[WorkspaceResourceReference, ...]
    attributes: Mapping[str, object]

    @classmethod
    def from_context(cls, context: ParticipantContext) -> ParticipantWorkspaceProjection:
        safe_attributes = {
            key: value
            for key, value in (context.attributes or {}).items()
            if not _is_hidden_key(key)
        }
        resources = tuple(
            WorkspaceResourceReference(
                resource_id=grant.resource_id,
                resource_type=grant.resource_type,
                access_mode=grant.access_mode,
                allowed_action_ids=grant.allowed_action_ids,
            )
            for grant in context.resource_access_grants
            if grant.access_mode is not ResourceAccessMode.NO_ACCESS
        )
        interactions = tuple(
            WorkspaceInteractionReference(
                recipient_id=relationship.target_id,
                interaction_types=relationship.allowed_interaction_types,
                relationship_type=relationship.relationship_type,
            )
            for relationship in context.relationships
            if relationship.source_id == context.actor_id
        )
        return cls(
            participant_id=context.participant_id,
            actor_id=context.actor_id,
            capabilities=context.capabilities,
            authorities=context.authorities,
            self_executable_action_ids=context.self_executable_action_ids,
            permitted_interaction_types=context.permitted_interaction_types,
            interactions=interactions,
            resources=resources,
            attributes=safe_attributes,
        )


@dataclass(frozen=True)
class SelectedResource:
    resource_id: str
    quantity: float | None = None
    capacity: float | None = None
    access_actor_id: str | None = None


@dataclass(frozen=True)
class EvaluationContext:
    actors: Mapping[str, ActorProfile]
    action_definitions: Mapping[str, ActionDefinition]
    relationships: tuple[Relationship, ...] = ()
    resource_profiles: Mapping[str, ResourceProfile] | None = None
    resource_snapshots: Mapping[str, ResourceStateSnapshot] | None = None
    task_demands: Mapping[str, TaskDemand] | None = None
    duration_policies: Mapping[str, DurationCalculationPolicy] | None = None
    attributes: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        policies = self.duration_policies or {}
        for action_definition in self.action_definitions.values():
            policy_id = (
                action_definition.work_profile.duration_policy_id
                if action_definition.work_profile is not None
                else None
            )
            if policy_id is not None and policy_id not in policies:
                raise DomainRuleViolation("Action duration policy reference is unavailable.")
        for task in (self.task_demands or {}).values():
            if task.action_definition_id not in self.action_definitions:
                raise DomainRuleViolation("Task demand action definition reference is unavailable.")
            if task.duration_policy_id is not None and task.duration_policy_id not in policies:
                raise DomainRuleViolation("Task demand duration policy reference is unavailable.")


@dataclass(frozen=True)
class CompatibilityInput:
    initiator_context: ParticipantContext
    intended_action_id: str
    intended_executor_id: str
    interaction_intent: InteractionIntent | None = None
    selected_resources: tuple[SelectedResource, ...] = ()
    prerequisite_states: Mapping[str, PrerequisiteStatus] | None = None
    evaluation_context: EvaluationContext | None = None


@dataclass(frozen=True)
class CompatibilityIssue:
    code: CompatibilityReasonCode
    requirement_id: str | None = None
    critical: bool = True


@dataclass(frozen=True)
class CompatibilityResult:
    compatible: bool
    outcome: CompatibilityOutcome
    reason_codes: tuple[CompatibilityReasonCode, ...]
    failed_requirement_ids: tuple[str, ...]
    critical_failures: tuple[CompatibilityIssue, ...]
    non_critical_warnings: tuple[CompatibilityIssue, ...]
    indeterminate_requirement_ids: tuple[str, ...]


class CompatibilityEvaluator:
    def evaluate(self, compatibility_input: CompatibilityInput) -> CompatibilityResult:
        issues: list[CompatibilityIssue] = []
        unknowns: list[str] = []
        context = compatibility_input.evaluation_context
        action = self._action(compatibility_input, context, issues)
        executor = self._executor(compatibility_input, context, issues)
        initiator = ActorProfile(
            id=compatibility_input.initiator_context.actor_id,
            capabilities=compatibility_input.initiator_context.capabilities,
            authorities=compatibility_input.initiator_context.authorities,
        )

        if action is not None:
            self._check_action_permission(compatibility_input, issues)
            if executor is not None:
                self._check_executor(action, executor, issues)
            self._check_initiation_authority(action, initiator, issues)
            self._check_interaction(compatibility_input, action, issues)
            self._check_prerequisites(action, compatibility_input, issues, unknowns)
            self._check_resources(compatibility_input, action, issues, unknowns)

        return self._result(issues, unknowns)

    @staticmethod
    def _action(
        compatibility_input: CompatibilityInput,
        context: EvaluationContext | None,
        issues: list[CompatibilityIssue],
    ) -> ActionDefinition | None:
        if context is None:
            issues.append(CompatibilityIssue(CompatibilityReasonCode.INSUFFICIENT_DATA))
            return None
        action = context.action_definitions.get(compatibility_input.intended_action_id)
        if action is None:
            issues.append(CompatibilityIssue(CompatibilityReasonCode.INSUFFICIENT_DATA))
        return action

    @staticmethod
    def _executor(
        compatibility_input: CompatibilityInput,
        context: EvaluationContext | None,
        issues: list[CompatibilityIssue],
    ) -> ActorProfile | None:
        if context is None:
            return None
        executor = context.actors.get(compatibility_input.intended_executor_id)
        if executor is None:
            issues.append(CompatibilityIssue(CompatibilityReasonCode.INSUFFICIENT_DATA))
        return executor

    @staticmethod
    def _check_action_permission(
        compatibility_input: CompatibilityInput,
        issues: list[CompatibilityIssue],
    ) -> None:
        if (
            compatibility_input.intended_action_id
            not in compatibility_input.initiator_context.self_executable_action_ids
        ):
            issues.append(
                CompatibilityIssue(
                    CompatibilityReasonCode.ACTION_NOT_PERMITTED,
                    compatibility_input.intended_action_id,
                )
            )

    @staticmethod
    def _check_executor(
        action: ActionDefinition,
        executor: ActorProfile,
        issues: list[CompatibilityIssue],
    ) -> None:
        missing_capabilities = set(action.required_capabilities) - set(executor.capabilities)
        for capability in sorted(missing_capabilities):
            issues.append(
                CompatibilityIssue(CompatibilityReasonCode.MISSING_CAPABILITY, capability)
            )
        missing_authorities = set(action.required_execution_authorities) - set(
            executor.authorities
        )
        for authority in sorted(missing_authorities):
            issues.append(CompatibilityIssue(CompatibilityReasonCode.MISSING_AUTHORITY, authority))

    @staticmethod
    def _check_initiation_authority(
        action: ActionDefinition,
        initiator: ActorProfile,
        issues: list[CompatibilityIssue],
    ) -> None:
        missing_authorities = set(action.required_initiation_authorities) - set(
            initiator.authorities
        )
        for authority in sorted(missing_authorities):
            issues.append(CompatibilityIssue(CompatibilityReasonCode.MISSING_AUTHORITY, authority))

    def _check_interaction(
        self,
        compatibility_input: CompatibilityInput,
        action: ActionDefinition,
        issues: list[CompatibilityIssue],
    ) -> None:
        intent = compatibility_input.interaction_intent
        if intent is None:
            return
        context = compatibility_input.initiator_context
        if intent.interaction_type not in context.permitted_interaction_types:
            issues.append(
                CompatibilityIssue(CompatibilityReasonCode.INTERACTION_NOT_PERMITTED)
            )
        if (
            action.permitted_interaction_types
            and intent.interaction_type not in action.permitted_interaction_types
        ):
            issues.append(
                CompatibilityIssue(CompatibilityReasonCode.INTERACTION_NOT_PERMITTED)
            )
        relationship_issue = self._relationship_issue(intent, context.relationships)
        if relationship_issue is not None:
            issues.append(relationship_issue)

    @staticmethod
    def _relationship_issue(
        intent: InteractionIntent, relationships: tuple[Relationship, ...]
    ) -> CompatibilityIssue | None:
        directed_match = [
            relationship
            for relationship in relationships
            if relationship.connects(intent.initiator_id, intent.recipient_id)
        ]
        if directed_match:
            if any(
                intent.interaction_type in relationship.allowed_interaction_types
                for relationship in directed_match
            ):
                return None
            return CompatibilityIssue(CompatibilityReasonCode.INTERACTION_NOT_PERMITTED)
        if any(
            relationship.connects_reverse(intent.initiator_id, intent.recipient_id)
            for relationship in relationships
        ):
            return CompatibilityIssue(CompatibilityReasonCode.INVALID_RELATIONSHIP_DIRECTION)
        return CompatibilityIssue(CompatibilityReasonCode.INVALID_RELATIONSHIP)

    @staticmethod
    def _check_prerequisites(
        action: ActionDefinition,
        compatibility_input: CompatibilityInput,
        issues: list[CompatibilityIssue],
        unknowns: list[str],
    ) -> None:
        states = compatibility_input.prerequisite_states or {}
        for prerequisite in action.prerequisites:
            state = states.get(prerequisite.id, PrerequisiteStatus.MISSING)
            if state is PrerequisiteStatus.SATISFIED:
                continue
            if state is PrerequisiteStatus.UNSATISFIED:
                issues.append(
                    CompatibilityIssue(
                        CompatibilityReasonCode.PREREQUISITE_UNMET,
                        prerequisite.id,
                        critical=prerequisite.criticality is RequirementCriticality.CRITICAL,
                    )
                )
            else:
                unknowns.append(prerequisite.id)

    def _check_resources(
        self,
        compatibility_input: CompatibilityInput,
        action: ActionDefinition,
        issues: list[CompatibilityIssue],
        unknowns: list[str],
    ) -> None:
        context = compatibility_input.evaluation_context
        if context is None:
            return
        profiles = context.resource_profiles or {}
        snapshots = context.resource_snapshots or {}
        selected_by_id = {resource.resource_id: resource for resource in compatibility_input.selected_resources}
        selected_profiles = tuple(
            profiles[resource_id]
            for resource_id in selected_by_id
            if resource_id in profiles
        )
        missing_profile_ids = set(selected_by_id) - set(profiles)
        for resource_id in sorted(missing_profile_ids):
            issues.append(CompatibilityIssue(CompatibilityReasonCode.INSUFFICIENT_DATA, resource_id))

        for requirement in action.resource_requirements:
            matching = tuple(
                profile for profile in selected_profiles if self._resource_matches(requirement, profile)
            )
            if not matching:
                issues.append(
                    CompatibilityIssue(
                        CompatibilityReasonCode.RESOURCE_MISMATCH,
                        requirement.id,
                        critical=requirement.criticality is RequirementCriticality.CRITICAL,
                    )
                )
                continue
            for profile in matching:
                selected = selected_by_id[profile.id]
                self._check_resource_access(compatibility_input, action, profile, issues)
                snapshot = snapshots.get(profile.id)
                if snapshot is None:
                    unknowns.append(requirement.id)
                    continue
                self._check_resource_snapshot(requirement, selected, snapshot, issues, unknowns)

    @staticmethod
    def _resource_matches(
        requirement: ResourceCommitmentRequirement, profile: ResourceProfile
    ) -> bool:
        if requirement.resource_ids and profile.id not in requirement.resource_ids:
            return False
        if requirement.resource_type is not None and profile.resource_type != requirement.resource_type:
            return False
        if not set(requirement.required_capabilities) <= set(profile.capabilities):
            return False
        required_properties = requirement.required_properties or {}
        properties = profile.properties or {}
        return all(properties.get(key) == value for key, value in required_properties.items())

    @staticmethod
    def _check_resource_access(
        compatibility_input: CompatibilityInput,
        action: ActionDefinition,
        profile: ResourceProfile,
        issues: list[CompatibilityIssue],
    ) -> None:
        actor_id = next(
            (
                selected.access_actor_id
                for selected in compatibility_input.selected_resources
                if selected.resource_id == profile.id and selected.access_actor_id is not None
            ),
            compatibility_input.intended_executor_id,
        )
        grants = tuple(
            grant
            for grant in compatibility_input.initiator_context.resource_access_grants
            if grant.actor_id == actor_id and grant.covers(profile, action.id)
        )
        if not grants:
            issues.append(CompatibilityIssue(CompatibilityReasonCode.RESOURCE_ACCESS_DENIED, profile.id))
            return
        grant = grants[0]
        if grant.access_mode is ResourceAccessMode.NO_ACCESS:
            issues.append(CompatibilityIssue(CompatibilityReasonCode.RESOURCE_ACCESS_DENIED, profile.id))
            return
        if grant.required_authority and grant.required_authority not in compatibility_input.initiator_context.authorities:
            issues.append(CompatibilityIssue(CompatibilityReasonCode.RESOURCE_ACCESS_REQUIREMENT_UNMET, profile.id))
        required_interaction = grant.required_interaction_type or _interaction_required_for(grant.access_mode)
        if required_interaction is not None:
            intent = compatibility_input.interaction_intent
            if intent is None or intent.interaction_type is not required_interaction:
                issues.append(
                    CompatibilityIssue(
                        CompatibilityReasonCode.RESOURCE_ACCESS_REQUIREMENT_UNMET,
                        profile.id,
                    )
                )

    @staticmethod
    def _check_resource_snapshot(
        requirement: ResourceCommitmentRequirement,
        selected: SelectedResource,
        snapshot: ResourceStateSnapshot,
        issues: list[CompatibilityIssue],
        unknowns: list[str],
    ) -> None:
        if snapshot.availability is ResourceAvailability.UNKNOWN:
            unknowns.append(requirement.id)
            return
        if snapshot.availability is not ResourceAvailability.AVAILABLE:
            issues.append(
                CompatibilityIssue(
                    CompatibilityReasonCode.RESOURCE_UNAVAILABLE,
                    requirement.id,
                    critical=requirement.criticality is RequirementCriticality.CRITICAL,
                )
            )
        if _fully_committed(snapshot):
            issues.append(
                CompatibilityIssue(
                    CompatibilityReasonCode.RESOURCE_ALREADY_COMMITTED,
                    requirement.id,
                    critical=requirement.criticality is RequirementCriticality.CRITICAL,
                )
            )
        quantity_needed = selected.quantity or requirement.minimum_quantity
        if quantity_needed is not None and snapshot.available_quantity is not None:
            if snapshot.available_quantity < quantity_needed:
                issues.append(
                    CompatibilityIssue(
                        CompatibilityReasonCode.INSUFFICIENT_RESOURCE_CAPACITY,
                        requirement.id,
                        critical=requirement.criticality is RequirementCriticality.CRITICAL,
                    )
                )
        capacity_needed = selected.capacity or requirement.minimum_capacity
        if capacity_needed is not None and snapshot.available_capacity is not None:
            if snapshot.available_capacity < capacity_needed:
                issues.append(
                    CompatibilityIssue(
                        CompatibilityReasonCode.INSUFFICIENT_RESOURCE_CAPACITY,
                        requirement.id,
                        critical=requirement.criticality is RequirementCriticality.CRITICAL,
                    )
                )

    @staticmethod
    def _result(
        issues: list[CompatibilityIssue],
        unknowns: list[str],
    ) -> CompatibilityResult:
        critical_failures = tuple(issue for issue in issues if issue.critical)
        warnings = tuple(issue for issue in issues if not issue.critical)
        if critical_failures:
            outcome = CompatibilityOutcome.INCOMPATIBLE
        elif unknowns:
            outcome = CompatibilityOutcome.INDETERMINATE
        elif warnings:
            outcome = CompatibilityOutcome.DEGRADED
        else:
            outcome = CompatibilityOutcome.COMPATIBLE
        return CompatibilityResult(
            compatible=outcome is CompatibilityOutcome.COMPATIBLE,
            outcome=outcome,
            reason_codes=tuple(dict.fromkeys(issue.code for issue in issues)),
            failed_requirement_ids=tuple(
                dict.fromkeys(
                    issue.requirement_id for issue in issues if issue.requirement_id is not None
                )
            ),
            critical_failures=critical_failures,
            non_critical_warnings=warnings,
            indeterminate_requirement_ids=tuple(dict.fromkeys(unknowns)),
        )


def _require_non_empty(value: str, label: str) -> None:
    if not value.strip():
        raise DomainRuleViolation(f"{label} must not be empty.")


def _require_unique(values: tuple[str, ...], label: str) -> None:
    if len(values) != len(set(values)):
        raise DomainRuleViolation(f"{label} must be unique.")
    for value in values:
        _require_non_empty(value, label)


def _require_non_negative_optional(value: float | int | None, label: str) -> None:
    if value is not None and value < 0:
        raise DomainRuleViolation(f"{label} cannot be negative.")


def _require_ordered_bounds(
    minimum: float | None, target: float | None, maximum: float | None, label: str
) -> None:
    if minimum is not None and target is not None and minimum > target:
        raise DomainRuleViolation(f"Minimum {label} cannot exceed target {label}.")
    if target is not None and maximum is not None and target > maximum:
        raise DomainRuleViolation(f"Target {label} cannot exceed maximum {label}.")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise DomainRuleViolation(f"Minimum {label} cannot exceed maximum {label}.")


def _interaction_required_for(access_mode: ResourceAccessMode) -> InteractionType | None:
    match access_mode:
        case ResourceAccessMode.REQUEST_REQUIRED:
            return InteractionType.REQUEST
        case ResourceAccessMode.ASSIGNMENT_REQUIRED:
            return InteractionType.ASSIGN
        case ResourceAccessMode.ORDER_REQUIRED:
            return InteractionType.ORDER
        case _:
            return None


def _fully_committed(snapshot: ResourceStateSnapshot) -> bool:
    if snapshot.active_commitment_refs and snapshot.available_capacity == 0:
        return True
    if snapshot.active_commitment_refs and snapshot.available_quantity == 0:
        return True
    if snapshot.current_capacity is not None and snapshot.committed_capacity is not None:
        return snapshot.committed_capacity >= snapshot.current_capacity
    if snapshot.current_quantity is not None and snapshot.committed_quantity is not None:
        return snapshot.committed_quantity >= snapshot.current_quantity
    return False


def _is_hidden_key(key: str) -> bool:
    normalized = key.replace("-", "_").replace(" ", "_").lower()
    compact = normalized.replace("_", "")
    return normalized.startswith("hidden_") or normalized in {
        "system_truth",
        "correct_solution",
        "correct_actor",
        "correct_resource",
        "targeting_metadata",
        "evaluator_rule",
    } or compact in {
        "systemtruth",
        "correctsolution",
        "correctactor",
        "correctresource",
        "targetingmetadata",
        "evaluatorrule",
    }
