from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.participant_capability import (
    ActionDefinition,
    ActionWorkProfile,
    ActorProfile,
    CompatibilityEvaluator,
    CompatibilityInput,
    CompatibilityOutcome,
    CompatibilityReasonCode,
    ConsumptionTiming,
    DurationCalculationPolicy,
    DurationCalculationStrategy,
    DurationEstimateStatus,
    DurationRoundingMode,
    EvaluationContext,
    InteractionIntent,
    InteractionType,
    ParticipantContext,
    ParticipantWorkspaceProjection,
    PrerequisiteStatus,
    Relationship,
    RelationshipDirection,
    Requirement,
    RequirementCriticality,
    RequirementKind,
    ResourceAccessGrant,
    ResourceAccessMode,
    ResourceAvailability,
    ResourceCommitmentRequirement,
    ResourceProfile,
    ResourceRenewalPolicy,
    ResourceStateSnapshot,
    SelectedResource,
    TaskDemand,
)


def actor(
    actor_id: str = "actor_a",
    capabilities: tuple[str, ...] = ("capability_x",),
    authorities: tuple[str, ...] = ("authority_execute", "authority_initiate"),
) -> ActorProfile:
    return ActorProfile(id=actor_id, capabilities=capabilities, authorities=authorities)


def action(
    action_id: str = "action_z",
    resource_requirement: ResourceCommitmentRequirement | None = None,
    prerequisites: tuple[Requirement, ...] = (),
    permitted_interactions: tuple[InteractionType, ...] = (),
    work_profile: ActionWorkProfile | None = None,
) -> ActionDefinition:
    return ActionDefinition(
        id=action_id,
        action_type="action_type_x",
        required_capabilities=("capability_x",),
        required_execution_authorities=("authority_execute",),
        required_initiation_authorities=("authority_initiate",),
        permitted_interaction_types=permitted_interactions,
        resource_requirements=(resource_requirement,) if resource_requirement else (),
        prerequisites=prerequisites,
        work_profile=work_profile,
    )


def resource_requirement(
    requirement_id: str = "requirement_resource_x",
    resource_type: str = "resource_type_x",
    minimum_quantity: float | None = 1,
    minimum_capacity: float | None = None,
    criticality: RequirementCriticality = RequirementCriticality.CRITICAL,
) -> ResourceCommitmentRequirement:
    return ResourceCommitmentRequirement(
        id=requirement_id,
        resource_type=resource_type,
        required_capabilities=("resource_capability_x",),
        required_properties={"property_x": "value_x"},
        minimum_quantity=minimum_quantity,
        minimum_capacity=minimum_capacity,
        criticality=criticality,
    )


def resource_profile(
    resource_id: str = "resource_x",
    resource_type: str = "resource_type_x",
    availability: ResourceAvailability = ResourceAvailability.AVAILABLE,
) -> ResourceProfile:
    return ResourceProfile(
        id=resource_id,
        resource_type=resource_type,
        capabilities=("resource_capability_x",),
        properties={"property_x": "value_x"},
        availability=availability,
        quantity=2,
        capacity=2,
        renewal_policy=ResourceRenewalPolicy.CONSUMABLE,
        owner_id="unit_x",
    )


def snapshot(
    resource_id: str = "resource_x",
    availability: ResourceAvailability = ResourceAvailability.AVAILABLE,
    current_quantity: float | None = 2,
    available_quantity: float | None = 2,
    committed_quantity: float | None = 0,
    current_capacity: float | None = 2,
    available_capacity: float | None = 2,
    committed_capacity: float | None = 0,
    commitments: tuple[str, ...] = (),
) -> ResourceStateSnapshot:
    return ResourceStateSnapshot(
        resource_id=resource_id,
        round_marker=1,
        current_quantity=current_quantity,
        available_quantity=available_quantity,
        committed_quantity=committed_quantity,
        current_capacity=current_capacity,
        available_capacity=available_capacity,
        committed_capacity=committed_capacity,
        availability=availability,
        active_commitment_refs=commitments,
    )


def relationship(
    source: str = "actor_a",
    target: str = "external_unit_y",
    interactions: tuple[InteractionType, ...] = (InteractionType.REQUEST,),
    direction: RelationshipDirection = RelationshipDirection.DIRECTED,
) -> Relationship:
    return Relationship(
        source_id=source,
        target_id=target,
        relationship_type="relationship_type_x",
        allowed_interaction_types=interactions,
        direction=direction,
    )


def participant_context(
    actor_id: str = "actor_a",
    actions: tuple[str, ...] = ("action_z",),
    interactions: tuple[InteractionType, ...] = (InteractionType.REQUEST, InteractionType.NOTIFY),
    relationships: tuple[Relationship, ...] = (relationship(),),
    grants: tuple[ResourceAccessGrant, ...] = (),
    authorities: tuple[str, ...] = ("authority_execute", "authority_initiate"),
) -> ParticipantContext:
    return ParticipantContext(
        participant_id="participant_a",
        actor_id=actor_id,
        session_id="session_x",
        capabilities=("capability_x",),
        authorities=authorities,
        self_executable_action_ids=actions,
        permitted_interaction_types=interactions,
        relationships=relationships,
        resource_access_grants=grants,
        attributes={"safe_attribute": "visible", "hidden_rule": "not_visible"},
    )


def direct_grant(resource_id: str = "resource_x", actor_id: str = "actor_a") -> ResourceAccessGrant:
    return ResourceAccessGrant(
        actor_id=actor_id,
        resource_id=resource_id,
        access_mode=ResourceAccessMode.DIRECT,
        allowed_action_ids=("action_z",),
    )


def request_grant(resource_id: str = "resource_x", actor_id: str = "actor_a") -> ResourceAccessGrant:
    return ResourceAccessGrant(
        actor_id=actor_id,
        resource_id=resource_id,
        access_mode=ResourceAccessMode.REQUEST_REQUIRED,
        allowed_action_ids=("action_z",),
        required_interaction_type=InteractionType.REQUEST,
    )


def evaluation_context(
    action_definition: ActionDefinition | None = None,
    actor_a: ActorProfile | None = None,
    actor_b: ActorProfile | None = None,
    resources: tuple[ResourceProfile, ...] = (resource_profile(),),
    snapshots: tuple[ResourceStateSnapshot, ...] = (snapshot(),),
    relationships: tuple[Relationship, ...] = (relationship(),),
) -> EvaluationContext:
    actors = {"actor_a": actor_a or actor(), "actor_b": actor_b or actor("actor_b")}
    return EvaluationContext(
        actors=actors,
        action_definitions={"action_z": action_definition or action()},
        relationships=relationships,
        resource_profiles={item.id: item for item in resources},
        resource_snapshots={item.resource_id: item for item in snapshots},
    )


def evaluate(
    context: ParticipantContext | None = None,
    action_definition: ActionDefinition | None = None,
    executor_id: str = "actor_a",
    selected: tuple[SelectedResource, ...] = (),
    interaction: InteractionIntent | None = None,
    states: dict[str, PrerequisiteStatus] | None = None,
    eval_context: EvaluationContext | None = None,
):
    participant = context or participant_context(grants=(direct_grant(),))
    context_for_evaluation = eval_context or evaluation_context(action_definition=action_definition)
    if eval_context is not None and action_definition is not None:
        context_for_evaluation = replace(
            eval_context, action_definitions={"action_z": action_definition}
        )
    return CompatibilityEvaluator().evaluate(
        CompatibilityInput(
            initiator_context=participant,
            intended_action_id="action_z",
            intended_executor_id=executor_id,
            interaction_intent=interaction,
            selected_resources=selected,
            prerequisite_states=states,
            evaluation_context=context_for_evaluation,
        )
    )


def test_participant_context_contains_allowed_personal_scope() -> None:
    context = participant_context(grants=(direct_grant(),))

    assert context.capabilities == ("capability_x",)
    assert context.authorities == ("authority_execute", "authority_initiate")
    assert context.self_executable_action_ids == ("action_z",)
    assert InteractionType.REQUEST in context.permitted_interaction_types
    assert context.resource_access_grants[0].access_mode is ResourceAccessMode.DIRECT


def test_workspace_projection_excludes_no_access_resources_and_hidden_attributes() -> None:
    context = participant_context(
        grants=(
            direct_grant("resource_x"),
            ResourceAccessGrant(
                actor_id="actor_a",
                resource_id="resource_hidden",
                access_mode=ResourceAccessMode.NO_ACCESS,
            ),
        )
    )

    projection = ParticipantWorkspaceProjection.from_context(context)

    assert tuple(item.resource_id for item in projection.resources) == ("resource_x",)
    assert projection.attributes == {"safe_attribute": "visible"}


def test_direct_resource_access_allows_use_without_interaction() -> None:
    result = evaluate(
        selected=(SelectedResource("resource_x", quantity=1),),
        action_definition=action(resource_requirement=resource_requirement()),
    )

    assert result.outcome is CompatibilityOutcome.COMPATIBLE


def test_request_required_without_request_reports_unmet_access_requirement() -> None:
    result = evaluate(
        context=participant_context(grants=(request_grant(),)),
        selected=(SelectedResource("resource_x", quantity=1),),
        action_definition=action(resource_requirement=resource_requirement()),
    )

    assert CompatibilityReasonCode.RESOURCE_ACCESS_REQUIREMENT_UNMET in result.reason_codes


def test_request_required_with_permitted_request_checks_access_then_resource_state() -> None:
    result = evaluate(
        context=participant_context(grants=(request_grant(),)),
        interaction=InteractionIntent("actor_a", "external_unit_y", InteractionType.REQUEST),
        selected=(SelectedResource("resource_x", quantity=1),),
        action_definition=action(
            resource_requirement=resource_requirement(),
            permitted_interactions=(InteractionType.REQUEST,),
        ),
    )

    assert CompatibilityReasonCode.RESOURCE_ACCESS_REQUIREMENT_UNMET not in result.reason_codes
    assert result.outcome is CompatibilityOutcome.COMPATIBLE


def test_actor_cannot_use_resource_only_because_it_exists_or_belongs_to_other_unit() -> None:
    result = evaluate(
        context=participant_context(grants=()),
        selected=(SelectedResource("resource_x", quantity=1),),
        action_definition=action(resource_requirement=resource_requirement()),
    )

    assert CompatibilityReasonCode.RESOURCE_ACCESS_DENIED in result.reason_codes


def test_executor_with_capability_and_execution_authority_is_compatible() -> None:
    result = evaluate()

    assert result.outcome is CompatibilityOutcome.COMPATIBLE


def test_missing_capability_is_reported() -> None:
    result = evaluate(eval_context=evaluation_context(actor_a=actor(capabilities=())))

    assert CompatibilityReasonCode.MISSING_CAPABILITY in result.reason_codes


def test_missing_execution_authority_is_reported() -> None:
    result = evaluate(eval_context=evaluation_context(actor_a=actor(authorities=("authority_initiate",))))

    assert CompatibilityReasonCode.MISSING_AUTHORITY in result.reason_codes


def test_notify_without_command_relationship_is_compatible_interaction() -> None:
    result = evaluate(
        context=participant_context(
            interactions=(InteractionType.NOTIFY,),
            relationships=(relationship(interactions=(InteractionType.NOTIFY,)),),
        ),
        interaction=InteractionIntent("actor_a", "external_unit_y", InteractionType.NOTIFY),
        action_definition=action(permitted_interactions=(InteractionType.NOTIFY,)),
    )

    assert CompatibilityReasonCode.INVALID_RELATIONSHIP not in result.reason_codes
    assert CompatibilityReasonCode.MISSING_AUTHORITY not in result.reason_codes


def test_request_to_external_unit_through_coordination_relationship_does_not_require_command() -> None:
    result = evaluate(
        context=participant_context(
            interactions=(InteractionType.REQUEST,),
            relationships=(relationship(interactions=(InteractionType.REQUEST,)),),
        ),
        interaction=InteractionIntent("actor_a", "external_unit_y", InteractionType.REQUEST),
        action_definition=action(permitted_interactions=(InteractionType.REQUEST,)),
    )

    assert result.outcome is CompatibilityOutcome.COMPATIBLE


def test_assign_without_authority_reports_missing_authority() -> None:
    result = evaluate(
        context=participant_context(
            interactions=(InteractionType.ASSIGN,),
            relationships=(relationship(interactions=(InteractionType.ASSIGN,)),),
            authorities=("authority_execute",),
        ),
        interaction=InteractionIntent("actor_a", "external_unit_y", InteractionType.ASSIGN),
        action_definition=action(permitted_interactions=(InteractionType.ASSIGN,)),
    )

    assert CompatibilityReasonCode.MISSING_AUTHORITY in result.reason_codes


def test_order_without_command_relationship_reports_invalid_relationship() -> None:
    result = evaluate(
        context=participant_context(interactions=(InteractionType.ORDER,), relationships=()),
        interaction=InteractionIntent("actor_a", "external_unit_y", InteractionType.ORDER),
        action_definition=action(permitted_interactions=(InteractionType.ORDER,)),
    )

    assert CompatibilityReasonCode.INVALID_RELATIONSHIP in result.reason_codes


def test_relationship_that_does_not_allow_interaction_reports_interaction_not_permitted() -> None:
    result = evaluate(
        context=participant_context(
            interactions=(InteractionType.ORDER,),
            relationships=(relationship(interactions=(InteractionType.REQUEST,)),),
        ),
        interaction=InteractionIntent("actor_a", "external_unit_y", InteractionType.ORDER),
        action_definition=action(permitted_interactions=(InteractionType.ORDER,)),
    )

    assert CompatibilityReasonCode.INTERACTION_NOT_PERMITTED in result.reason_codes


def test_reverse_direction_relationship_is_not_assumed_valid() -> None:
    result = evaluate(
        context=participant_context(
            relationships=(relationship(source="external_unit_y", target="actor_a"),),
            grants=(direct_grant(),),
        ),
        interaction=InteractionIntent("actor_a", "external_unit_y", InteractionType.REQUEST),
        action_definition=action(permitted_interactions=(InteractionType.REQUEST,)),
    )

    assert CompatibilityReasonCode.INVALID_RELATIONSHIP_DIRECTION in result.reason_codes


def test_valid_interaction_and_incompetent_executor_are_separate_checks() -> None:
    result = evaluate(
        interaction=InteractionIntent("actor_a", "external_unit_y", InteractionType.REQUEST),
        action_definition=action(permitted_interactions=(InteractionType.REQUEST,)),
        eval_context=evaluation_context(actor_a=actor(capabilities=())),
    )

    assert CompatibilityReasonCode.INVALID_RELATIONSHIP not in result.reason_codes
    assert CompatibilityReasonCode.MISSING_CAPABILITY in result.reason_codes


def test_wrong_resource_type_or_property_reports_resource_mismatch() -> None:
    result = evaluate(
        selected=(SelectedResource("resource_x", quantity=1),),
        action_definition=action(resource_requirement=resource_requirement(resource_type="resource_type_y")),
    )

    assert CompatibilityReasonCode.RESOURCE_MISMATCH in result.reason_codes


def test_matching_but_unavailable_resource_reports_resource_unavailable() -> None:
    result = evaluate(
        selected=(SelectedResource("resource_x", quantity=1),),
        action_definition=action(resource_requirement=resource_requirement()),
        eval_context=evaluation_context(snapshots=(snapshot(availability=ResourceAvailability.UNAVAILABLE),)),
    )

    assert CompatibilityReasonCode.RESOURCE_UNAVAILABLE in result.reason_codes


def test_insufficient_quantity_or_capacity_is_reported() -> None:
    result = evaluate(
        selected=(SelectedResource("resource_x", quantity=2),),
        action_definition=action(resource_requirement=resource_requirement(minimum_quantity=2)),
        eval_context=evaluation_context(snapshots=(snapshot(available_quantity=1),)),
    )

    assert CompatibilityReasonCode.INSUFFICIENT_RESOURCE_CAPACITY in result.reason_codes


def test_fully_committed_human_or_equipment_resource_is_not_reused() -> None:
    result = evaluate(
        selected=(SelectedResource("resource_x", capacity=1),),
        action_definition=action(
            resource_requirement=resource_requirement(minimum_quantity=None, minimum_capacity=1)
        ),
        eval_context=evaluation_context(
            snapshots=(
                snapshot(
                    current_capacity=1,
                    available_capacity=0,
                    committed_capacity=1,
                    commitments=("work_instance_existing",),
                ),
            )
        ),
    )

    assert CompatibilityReasonCode.RESOURCE_ALREADY_COMMITTED in result.reason_codes


def test_action_can_describe_multi_round_duration_without_runtime_execution() -> None:
    work = ActionWorkProfile(fixed_duration_rounds=3, required_work_units=12)
    action_definition = action(work_profile=work)

    result = evaluate(action_definition=action_definition)

    assert action_definition.work_profile == work
    assert result.outcome is CompatibilityOutcome.COMPATIBLE


def test_consumable_resource_policy_is_described_without_quantity_mutation() -> None:
    before = snapshot(current_quantity=5, available_quantity=5)
    result = evaluate(
        selected=(SelectedResource("resource_x", quantity=2),),
        action_definition=action(
            resource_requirement=ResourceCommitmentRequirement(
                id="requirement_resource_x",
                resource_type="resource_type_x",
                required_capabilities=("resource_capability_x",),
                required_properties={"property_x": "value_x"},
                minimum_quantity=2,
                consumption_timing=ConsumptionTiming.ON_START,
            )
        ),
        eval_context=evaluation_context(snapshots=(before,)),
    )

    assert result.outcome is CompatibilityOutcome.COMPATIBLE
    assert before.available_quantity == 5


def test_two_task_instances_same_action_type_can_have_different_demands() -> None:
    task_a = TaskDemand("task_a", "action_z", required_work_units=2, remaining_work_units=2)
    task_b = TaskDemand("task_b", "action_z", required_work_units=8, remaining_work_units=8)

    assert task_a.required_work_units != task_b.required_work_units
    assert task_a.action_definition_id == task_b.action_definition_id


def test_additional_resource_contribution_is_data_not_optimizer() -> None:
    requirement = ResourceCommitmentRequirement(
        id="requirement_resource_x",
        resource_type="resource_type_x",
        required_capabilities=("resource_capability_x",),
        required_properties={"property_x": "value_x"},
        minimum_quantity=1,
        target_quantity=2,
        productivity_units=1,
        additional_resources_reduce_duration=True,
    )

    result = evaluate(
        selected=(SelectedResource("resource_x", quantity=1),),
        action_definition=action(resource_requirement=requirement),
    )

    assert result.outcome is CompatibilityOutcome.COMPATIBLE
    assert requirement.additional_resources_reduce_duration is True


def test_new_simultaneous_task_does_not_release_committed_resource() -> None:
    result = evaluate(
        selected=(SelectedResource("resource_x", capacity=1),),
        action_definition=action(
            resource_requirement=resource_requirement(minimum_quantity=None, minimum_capacity=1)
        ),
        eval_context=evaluation_context(
            snapshots=(snapshot(available_capacity=0, committed_capacity=2, current_capacity=2),)
        ),
    )

    assert CompatibilityReasonCode.RESOURCE_ALREADY_COMMITTED in result.reason_codes


def test_critical_unmet_prerequisite_is_incompatible() -> None:
    prerequisite = Requirement(
        "prerequisite_x",
        RequirementKind.PREREQUISITE,
        True,
        RequirementCriticality.CRITICAL,
    )
    result = evaluate(
        action_definition=action(prerequisites=(prerequisite,)),
        states={"prerequisite_x": PrerequisiteStatus.UNSATISFIED},
    )

    assert result.outcome is CompatibilityOutcome.INCOMPATIBLE
    assert CompatibilityReasonCode.PREREQUISITE_UNMET in result.reason_codes


def test_non_critical_mismatch_is_degraded() -> None:
    prerequisite = Requirement(
        "prerequisite_x",
        RequirementKind.PREREQUISITE,
        True,
        RequirementCriticality.NON_CRITICAL,
    )
    result = evaluate(
        action_definition=action(prerequisites=(prerequisite,)),
        states={"prerequisite_x": PrerequisiteStatus.UNSATISFIED},
    )

    assert result.outcome is CompatibilityOutcome.DEGRADED
    assert result.non_critical_warnings


def test_unknown_prerequisite_is_indeterminate() -> None:
    prerequisite = Requirement("prerequisite_x", RequirementKind.PREREQUISITE, True)
    result = evaluate(action_definition=action(prerequisites=(prerequisite,)))

    assert result.outcome is CompatibilityOutcome.INDETERMINATE
    assert result.indeterminate_requirement_ids == ("prerequisite_x",)


def test_missing_resource_snapshot_is_not_treated_as_available() -> None:
    result = evaluate(
        selected=(SelectedResource("resource_x", quantity=1),),
        action_definition=action(resource_requirement=resource_requirement()),
        eval_context=evaluation_context(snapshots=()),
    )

    assert result.outcome is CompatibilityOutcome.INDETERMINATE
    assert "requirement_resource_x" in result.indeterminate_requirement_ids


def test_multiple_independent_violations_are_returned_together() -> None:
    result = evaluate(
        context=participant_context(actions=(), grants=()),
        eval_context=evaluation_context(actor_a=actor(capabilities=(), authorities=())),
        action_definition=action(resource_requirement=resource_requirement()),
        selected=(SelectedResource("resource_x", quantity=1),),
    )

    assert CompatibilityReasonCode.ACTION_NOT_PERMITTED in result.reason_codes
    assert CompatibilityReasonCode.MISSING_CAPABILITY in result.reason_codes
    assert CompatibilityReasonCode.MISSING_AUTHORITY in result.reason_codes
    assert CompatibilityReasonCode.RESOURCE_ACCESS_DENIED in result.reason_codes


def test_critical_failure_plus_unknown_is_incompatible_and_keeps_unknown() -> None:
    prerequisite = Requirement("prerequisite_x", RequirementKind.PREREQUISITE, True)
    result = evaluate(
        context=participant_context(actions=(), grants=(direct_grant(),)),
        action_definition=action(prerequisites=(prerequisite,)),
    )

    assert result.outcome is CompatibilityOutcome.INCOMPATIBLE
    assert "prerequisite_x" in result.indeterminate_requirement_ids


def test_seven_arbitrary_actors_work_without_hardcoding() -> None:
    actors = {f"actor_{index}": actor(f"actor_{index}") for index in range(6)}
    actors["actor_a"] = actor("actor_a")

    result = evaluate(eval_context=EvaluationContext(actors=actors, action_definitions={"action_z": action()}))

    assert len(actors) == 7
    assert result.outcome is CompatibilityOutcome.COMPATIBLE


def test_other_actor_counts_work_without_hardcoding() -> None:
    actors = {f"actor_{index}": actor(f"actor_{index}") for index in range(3)}
    actors["actor_a"] = actor("actor_a")

    result = evaluate(eval_context=EvaluationContext(actors=actors, action_definitions={"action_z": action()}))

    assert len(actors) == 4
    assert result.outcome is CompatibilityOutcome.COMPATIBLE


def test_arbitrary_identifiers_do_not_require_production_code_changes() -> None:
    result = evaluate(
        context=participant_context(actor_id="actor_custom", grants=(direct_grant(actor_id="actor_custom"),)),
        eval_context=EvaluationContext(
            actors={"actor_custom": actor("actor_custom")},
            action_definitions={"action_z": action()},
        ),
        executor_id="actor_custom",
    )

    assert result.outcome is CompatibilityOutcome.COMPATIBLE


def test_workspace_projection_and_result_do_not_reveal_correct_solution() -> None:
    projection = ParticipantWorkspaceProjection.from_context(participant_context(grants=(direct_grant(),)))
    result = evaluate()

    assert "correct_solution" not in projection.attributes
    assert not hasattr(result, "recommended_actor_id")
    assert not hasattr(result, "candidate_resource_ids")


def test_legacy_opaque_payload_remains_compatible_with_pr13_api() -> None:
    client = TestClient(app)
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Facilitator",
            "player_capacity": 1,
            "role_profiles": [
                {
                    "role_id": role_id,
                    "title": "role_x",
                    "category": "category_x",
                    "briefing": "briefing_x",
                }
            ],
        },
    )
    body = created.json()
    facilitator_headers = {"X-Facilitator-Token": body["facilitator_token"]}
    joined = client.post(
        f"/sessions/{body['id']}/participants/join",
        json={"join_token": body["join_token"], "display_name": "participant_x"},
    )
    participant = joined.json()
    client.put(
        f"/sessions/{body['id']}/participants/{participant['participant_id']}/role",
        json={"role_id": role_id},
        headers=facilitator_headers,
    )
    client.post(f"/sessions/{body['id']}/start", headers=facilitator_headers)
    inject = client.post(
        f"/sessions/{body['id']}/injects",
        json={"title": "inject_x", "description": "inject_description_x", "payload": {}},
        headers=facilitator_headers,
    ).json()
    payload = {"kind": "opaque_x", "content": {"value": "kept"}}

    submitted = client.post(
        f"/sessions/{body['id']}/injects/{inject['id']}/decisions",
        json={"participant_id": participant["participant_id"], "decision_payload": payload},
        headers={"X-Participant-Token": participant["participant_token"]},
    )

    assert submitted.status_code == 200
    assert submitted.json()["decision_payload"] == payload


def test_structurally_valid_but_semantically_incompatible_payload_is_not_http_422() -> None:
    client = TestClient(app)
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Facilitator",
            "player_capacity": 1,
            "role_profiles": [
                {
                    "role_id": role_id,
                    "title": "role_x",
                    "category": "category_x",
                    "briefing": "briefing_x",
                }
            ],
        },
    )
    body = created.json()
    facilitator_headers = {"X-Facilitator-Token": body["facilitator_token"]}
    joined = client.post(
        f"/sessions/{body['id']}/participants/join",
        json={"join_token": body["join_token"], "display_name": "participant_x"},
    )
    participant = joined.json()
    client.put(
        f"/sessions/{body['id']}/participants/{participant['participant_id']}/role",
        json={"role_id": role_id},
        headers=facilitator_headers,
    )
    client.post(f"/sessions/{body['id']}/start", headers=facilitator_headers)
    inject = client.post(
        f"/sessions/{body['id']}/injects",
        json={"title": "inject_x", "description": "inject_description_x", "payload": {}},
        headers=facilitator_headers,
    ).json()
    payload = {
        "schema_version": "participant-decision-lego-1.0",
        "kind": "lego_decision",
        "blocks": [
            {
                "block_id": "block_action_x",
                "block_type": "action",
                "label": "action_z",
                "data": {"semantic_issue": "wrong_resource_x"},
            }
        ],
        "links": [],
        "metadata": {"created_by": "participant_workspace"},
    }

    submitted = client.post(
        f"/sessions/{body['id']}/injects/{inject['id']}/decisions",
        json={"participant_id": participant["participant_id"], "decision_payload": payload},
        headers={"X-Participant-Token": participant["participant_token"]},
    )

    assert submitted.status_code == 200


def duration_policy(policy_id: str = "duration_policy_x") -> DurationCalculationPolicy:
    return DurationCalculationPolicy(
        id=policy_id,
        strategy=DurationCalculationStrategy.WORK_OVER_PRODUCTIVITY,
        work_unit="work_unit_x",
        productivity_unit="productivity_unit_x_per_round",
        time_unit="round",
        rounding=DurationRoundingMode.CEIL,
        minimum_effective_productivity=0,
        maximum_effective_productivity=10,
        modifier_keys=("complexity_x", "severity_x"),
        supports_diminishing_returns=True,
        supports_dependency=True,
        supports_synergy=True,
    )


def test_event_or_action_type_can_reference_duration_policy_without_hardcoded_event_names() -> None:
    policy = duration_policy()
    work = ActionWorkProfile(
        required_work_units=10,
        duration_policy_id="duration_policy_x",
        contextual_modifiers={"complexity_x": 2},
    )
    action_definition = action(work_profile=work)
    context = EvaluationContext(
        actors={"actor_a": actor()},
        action_definitions={"action_z": action_definition},
        duration_policies={"duration_policy_x": policy},
    )

    assert context.action_definitions["action_z"].work_profile is work
    assert policy.strategy is DurationCalculationStrategy.WORK_OVER_PRODUCTIVITY
    assert policy.rounding is DurationRoundingMode.CEIL


def test_participant_does_not_submit_freeform_duration_as_correct_answer() -> None:
    work = ActionWorkProfile(required_work_units=6, duration_policy_id="duration_policy_x")
    task = TaskDemand(
        id="task_x",
        action_definition_id="action_z",
        required_work_units=6,
        remaining_work_units=4,
        duration_policy_id="duration_policy_x",
    )

    assert work.duration_policy_id == "duration_policy_x"
    assert task.remaining_work_units == 4
    assert not hasattr(task, "participant_entered_duration_rounds")


def test_duration_policy_supports_basic_work_over_productivity_config_without_executing_it() -> None:
    policy = duration_policy()
    requirement = ResourceCommitmentRequirement(
        id="requirement_resource_x",
        resource_type="resource_type_x",
        productivity_units=2,
        minimum_capacity=1,
    )
    work = ActionWorkProfile(
        required_work_units=8,
        duration_policy_id=policy.id,
        resource_commitments=(requirement,),
    )

    assert work.required_work_units == 8
    assert requirement.productivity_units == 2
    assert not hasattr(policy, "estimate_rounds")


def test_resource_allocation_can_change_future_duration_inputs_without_changing_action_type() -> None:
    policy = duration_policy()
    action_definition = action(
        work_profile=ActionWorkProfile(required_work_units=8, duration_policy_id=policy.id),
    )
    task_a = TaskDemand("task_a", "action_z", remaining_work_units=8, duration_policy_id=policy.id)
    task_b = TaskDemand("task_b", "action_z", remaining_work_units=3, duration_policy_id=policy.id)

    assert action_definition.action_type == "action_type_x"
    assert task_a.remaining_work_units != task_b.remaining_work_units
    assert task_a.duration_policy_id == task_b.duration_policy_id


def test_zero_productivity_and_unknown_inputs_are_representable_without_fake_duration() -> None:
    policy = DurationCalculationPolicy(
        id="duration_policy_x",
        strategy=DurationCalculationStrategy.WORK_OVER_PRODUCTIVITY,
        work_unit="work_unit_x",
        productivity_unit="productivity_unit_x_per_round",
        allow_zero_productivity_result=False,
        blocked_status=DurationEstimateStatus.BLOCKED,
        insufficient_data_status=DurationEstimateStatus.INSUFFICIENT_DATA,
    )
    requirement = ResourceCommitmentRequirement(
        id="requirement_resource_x",
        resource_type="resource_type_x",
        productivity_units=0,
        criticality=RequirementCriticality.CRITICAL,
    )

    assert policy.allow_zero_productivity_result is False
    assert policy.blocked_status is DurationEstimateStatus.BLOCKED
    assert policy.insufficient_data_status is DurationEstimateStatus.INSUFFICIENT_DATA
    assert requirement.productivity_units == 0


def test_duration_policy_structural_validation_rejects_bad_units_ranges_and_references() -> None:
    with pytest.raises(DomainRuleViolation):
        DurationCalculationPolicy(
            id="duration_policy_x",
            strategy=DurationCalculationStrategy.WORK_OVER_PRODUCTIVITY,
            work_unit="",
            productivity_unit="productivity_unit_x_per_round",
        )
    with pytest.raises(DomainRuleViolation):
        DurationCalculationPolicy(
            id="duration_policy_x",
            strategy=DurationCalculationStrategy.WORK_OVER_PRODUCTIVITY,
            work_unit="work_unit_x",
            productivity_unit="productivity_unit_x_per_round",
            minimum_effective_productivity=5,
            maximum_effective_productivity=2,
        )
    with pytest.raises(DomainRuleViolation):
        ResourceCommitmentRequirement(
            id="requirement_resource_x",
            minimum_quantity=5,
            target_quantity=2,
        )
    with pytest.raises(DomainRuleViolation):
        EvaluationContext(
            actors={"actor_a": actor()},
            action_definitions={
                "action_z": action(
                    work_profile=ActionWorkProfile(duration_policy_id="missing_policy_x")
                )
            },
            duration_policies={},
        )


def test_duration_policy_configuration_contains_no_ready_made_solution_route() -> None:
    policy = duration_policy()
    result = evaluate()

    assert not hasattr(policy, "correct_actor_id")
    assert not hasattr(policy, "recommended_action_sequence")
    assert not hasattr(policy, "hidden_route")
    assert result.outcome is CompatibilityOutcome.COMPATIBLE

