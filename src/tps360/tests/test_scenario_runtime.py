from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    Scenario,
    ScenarioCompatibilityPolicy,
    ScenarioDefinition,
    ScenarioDifficulty,
    ScenarioGoal,
    ScenarioMetadata,
    ScenarioPhase,
    ScenarioRuntimeStatus,
    ScenarioType,
    ScenarioValidationLevel,
    Simulation,
    SimulationClock,
    SimulationContext,
    SimulationStatus,
    Timeline,
    TimelineEvent,
)
from tps360.threats.domain import Threat, ThreatSeverity, ThreatTargetType, ThreatType

START = datetime(2026, 7, 24, 9, 0)
RESOURCE_ID = UUID("11111111-1111-1111-1111-111111111111")


def build_definition(**overrides: object) -> ScenarioDefinition:
    values: dict[str, object] = {
        "id": UUID("22222222-2222-2222-2222-222222222222"),
        "name": "Power outage response",
        "description": "Coordinate response to a power outage.",
        "version": 1,
        "scenario_type": ScenarioType.TECHNOLOGICAL,
        "difficulty": ScenarioDifficulty.MODERATE,
        "initial_conditions": ("Power is unavailable.",),
        "simulation_goals": (ScenarioGoal(UUID("33333333-3333-3333-3333-333333333333"), "Restore power."),),
        "completion_criteria": ("power_restored",),
        "initial_threat_ids": (UUID("44444444-4444-4444-4444-444444444444"),),
        "planned_events": (
            TimelineEvent(
                id=UUID("55555555-5555-5555-5555-555555555555"),
                timestamp=START + timedelta(minutes=10),
                name="Escalation",
                description="The outage expands.",
            ),
        ),
        "allowed_team_roles": ("coordinator",),
        "metadata": ScenarioMetadata(author="TPS360", source="exercise handbook"),
        "phases": (
            ScenarioPhase("PRE_CRISIS"),
            ScenarioPhase("ESCALATION"),
            ScenarioPhase("ACTIVE_RESPONSE"),
        ),
        "required_territories": ("Central",),
        "required_infrastructure": ("substation",),
        "required_resource_ids": (RESOURCE_ID,),
        "supported_threat_types": (ThreatType.TECHNOLOGICAL,),
    }
    values.update(overrides)
    return ScenarioDefinition(**values)  # type: ignore[arg-type]


def build_context() -> SimulationContext:
    return SimulationContext(
        id=uuid4(),
        community_id=str(uuid4()),
        community_profile_id=uuid4(),
        community_profile_version="1.0.0",
        community_map_id=uuid4(),
        community_map_version=1,
        scenario_id=uuid4(),
        scenario_version=1,
        primary_threat_id=uuid4(),
        available_resource_ids=(RESOURCE_ID,),
        participating_organization_ids=(uuid4(),),
        data_quality_score=80.0,
        created_at=START,
        checksum="checksum",
    )


def build_simulation(**overrides: object) -> Simulation:
    values: dict[str, object] = {
        "id": uuid4(),
        "scenario": Scenario(
            id=uuid4(),
            name="Session",
            description="Scenario runtime session.",
        ),
        "community": Community(
            name="Example",
            code="EX",
            oblast="Kyiv",
            population=1,
            area_km2=1.0,
            settlements=["Central"],
            critical_infrastructure=["substation"],
        ),
        "threat": Threat(
            id=uuid4(),
            name="Power outage",
            threat_type=ThreatType.TECHNOLOGICAL,
            severity=ThreatSeverity.HIGH,
            target_type=ThreatTargetType.CRITICAL_INFRASTRUCTURE,
            description="Loss of electrical power.",
        ),
        "timeline": Timeline(),
        "current_time": START,
        "status": SimulationStatus.DRAFT,
        "clock": SimulationClock(start_time=START, current_time=START),
        "context": build_context(),
    }
    values.update(overrides)
    return Simulation(**values)  # type: ignore[arg-type]


def load_and_validate(simulation: Simulation, definition: ScenarioDefinition) -> None:
    simulation.load_scenario(definition)
    simulation.validate_scenario(("coordinator",))


def activate(simulation: Simulation, definition: ScenarioDefinition) -> None:
    simulation.prepare()
    load_and_validate(simulation, definition)
    simulation.activate_scenario()


def test_valid_scenario_definition() -> None:
    assert build_definition().version == 1


def test_scenario_definition_is_immutable() -> None:
    definition = build_definition()

    with pytest.raises(FrozenInstanceError):
        definition.name = "Changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "scenario_type",
    [
        ScenarioType.MILITARY,
        ScenarioType.TECHNOLOGICAL,
        ScenarioType.NATURAL,
        ScenarioType.HUMANITARIAN,
        ScenarioType.COMBINED,
    ],
)
def test_all_scenario_types_are_supported(scenario_type: ScenarioType) -> None:
    assert build_definition(scenario_type=scenario_type).scenario_type is scenario_type


def test_loading_creates_runtime_with_event() -> None:
    simulation = build_simulation()

    runtime = simulation.load_scenario(build_definition())

    assert runtime.status is ScenarioRuntimeStatus.LOADED
    assert runtime.audit_trail[-1].scenario_id == runtime.definition.id


def test_validation_returns_structured_errors_for_incompatible_snapshot() -> None:
    simulation = build_simulation()
    definition = build_definition(required_resource_ids=(uuid4(),))
    simulation.load_scenario(definition)

    result = simulation.validate_scenario(("coordinator",))

    assert result.errors[0].level is ScenarioValidationLevel.ERROR
    assert not result.can_activate


def test_validation_warnings_do_not_block_activation() -> None:
    definition = build_definition(planned_events=(), completion_criteria=())
    simulation = build_simulation()
    simulation.prepare()
    load_and_validate(simulation, definition)

    simulation.activate_scenario()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.status is ScenarioRuntimeStatus.ACTIVE
    assert simulation.scenario_runtime.validation_result is not None
    assert simulation.scenario_runtime.validation_result.warnings


def test_compatible_scenario_activates_only_in_prepared_session() -> None:
    simulation = build_simulation()
    load_and_validate(simulation, build_definition())

    with pytest.raises(DomainRuleViolation):
        simulation.activate_scenario()

    simulation.prepare()
    simulation.activate_scenario()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.activated_at == START


def test_incompatible_scenario_cannot_activate() -> None:
    simulation = build_simulation()
    simulation.prepare()
    simulation.load_scenario(build_definition(required_territories=("Missing",)))
    simulation.validate_scenario(("coordinator",))

    with pytest.raises(DomainRuleViolation):
        simulation.activate_scenario()


def test_loaded_validated_active_suspended_resumed_transitions() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())

    simulation.suspend_scenario()
    simulation.resume_scenario()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.status is ScenarioRuntimeStatus.ACTIVE


def test_active_scenario_can_complete_when_criteria_are_met() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())
    simulation.mark_scenario_completion_criterion("power_restored")

    simulation.complete_scenario()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.status is ScenarioRuntimeStatus.COMPLETED


def test_active_scenario_can_fail() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())

    simulation.fail_scenario()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.status is ScenarioRuntimeStatus.FAILED


@pytest.mark.parametrize("status", [SimulationStatus.DRAFT, SimulationStatus.READY, SimulationStatus.RUNNING])
def test_unfinished_runtime_can_be_cancelled(status: SimulationStatus) -> None:
    simulation = build_simulation(status=status)
    simulation.load_scenario(build_definition())

    simulation.cancel_scenario()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.status is ScenarioRuntimeStatus.CANCELLED


def test_invalid_runtime_transition_is_rejected() -> None:
    simulation = build_simulation()
    simulation.load_scenario(build_definition())

    with pytest.raises(DomainRuleViolation):
        simulation.advance_scenario_phase()


def test_phases_advance_in_order() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())

    simulation.advance_scenario_phase()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.current_phase == "ESCALATION"


def test_required_phase_cannot_be_skipped() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())

    assert simulation.scenario_runtime is not None
    with pytest.raises(DomainRuleViolation):
        simulation.move_scenario_to_phase("ACTIVE_RESPONSE")


def test_last_phase_does_not_auto_complete_runtime() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())

    simulation.advance_scenario_phase()
    simulation.advance_scenario_phase()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.status is ScenarioRuntimeStatus.ACTIVE


def test_final_runtime_cannot_change() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())
    simulation.mark_scenario_completion_criterion("power_restored")
    simulation.complete_scenario()

    with pytest.raises(DomainRuleViolation):
        simulation.advance_scenario_phase()


def test_runtime_events_and_audit_trail_are_recorded() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())
    simulation.suspend_scenario()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.audit_trail == simulation.scenario_runtime.domain_events
    assert simulation.scenario_runtime.audit_trail[-1].occurred_at == START


def test_runtime_behavior_is_deterministic() -> None:
    first = build_simulation()
    second = build_simulation()
    definition = build_definition()

    activate(first, definition)
    activate(second, definition)
    first.advance_scenario_phase()
    second.advance_scenario_phase()

    assert first.scenario_runtime is not None
    assert second.scenario_runtime is not None
    assert first.scenario_runtime.current_phase == second.scenario_runtime.current_phase


def test_two_simulations_get_independent_runtimes_for_same_definition() -> None:
    definition = build_definition()
    first = build_simulation()
    second = build_simulation()

    activate(first, definition)
    activate(second, definition)
    first.advance_scenario_phase()

    assert first.scenario_runtime is not None
    assert second.scenario_runtime is not None
    assert first.scenario_runtime is not second.scenario_runtime
    assert second.scenario_runtime.current_phase == "PRE_CRISIS"


def test_base_community_profile_remains_unchanged() -> None:
    simulation = build_simulation()
    original_community = simulation.community.model_dump()

    activate(simulation, build_definition())
    simulation.advance_scenario_phase()

    assert simulation.community.model_dump() == original_community


def test_only_one_main_scenario_runtime_can_be_loaded() -> None:
    simulation = build_simulation()
    simulation.load_scenario(build_definition())

    with pytest.raises(DomainRuleViolation):
        simulation.load_scenario(build_definition(id=uuid4()))


def test_policy_does_not_use_system_time() -> None:
    result = ScenarioCompatibilityPolicy.validate(
        build_definition(),
        build_simulation(),
        ("coordinator",),
    )

    assert result.can_activate
@pytest.mark.parametrize("runtime_state", ["loaded", "validated", "active", "suspended"])
def test_runtime_can_be_cancelled_from_every_unfinished_status(runtime_state: str) -> None:
    simulation = build_simulation()
    definition = build_definition()
    simulation.load_scenario(definition)
    if runtime_state != "loaded":
        simulation.validate_scenario(("coordinator",))
    if runtime_state in {"active", "suspended"}:
        simulation.prepare()
        simulation.activate_scenario()
    if runtime_state == "suspended":
        simulation.suspend_scenario()

    simulation.cancel_scenario()

    assert simulation.scenario_runtime is not None
    assert simulation.scenario_runtime.status is ScenarioRuntimeStatus.CANCELLED


def test_final_runtime_rejects_direct_state_change() -> None:
    simulation = build_simulation()
    activate(simulation, build_definition())
    simulation.mark_scenario_completion_criterion("power_restored")
    simulation.complete_scenario()

    assert simulation.scenario_runtime is not None
    with pytest.raises(DomainRuleViolation):
        simulation.scenario_runtime.active_conditions = ("changed",)