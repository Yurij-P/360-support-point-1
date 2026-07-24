from dataclasses import FrozenInstanceError
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    ImpactCategory,
    ImpactChange,
    ImpactConflictPolicy,
    ImpactDefinition,
    ImpactOperation,
    ImpactSourceType,
    ImpactStatus,
    ImpactTarget,
    ImpactTargetType,
    Scenario,
    ScenarioDefinition,
    ScenarioDifficulty,
    ScenarioGoal,
    ScenarioMetadata,
    ScenarioPhase,
    ScenarioType,
    Simulation,
    SimulationClock,
    SimulationContext,
    SimulationState,
    StateKey,
    StateValue,
    Timeline,
)
from tps360.threats.domain import Threat, ThreatSeverity, ThreatTargetType, ThreatType

START = datetime(2026, 7, 25, 9, 0)
SCENARIO_ID = UUID("22222222-2222-2222-2222-222222222222")
RESOURCE_ID = UUID("11111111-1111-1111-1111-111111111111")
SOURCE_ID = UUID("33333333-3333-3333-3333-333333333333")


def sim() -> Simulation:
    result = Simulation(
        id=uuid4(), scenario=Scenario(uuid4(), "Session", "Impact session."),
        community=Community(name="Example", code="EX", oblast="Kyiv", population=1, area_km2=1.0),
        threat=Threat(uuid4(), "Power loss", ThreatType.TECHNOLOGICAL, ThreatSeverity.HIGH, ThreatTargetType.CRITICAL_INFRASTRUCTURE, "Power loss."),
        timeline=Timeline(), current_time=START, status=__import__('tps360.simulation.domain', fromlist=['SimulationStatus']).SimulationStatus.DRAFT,
        clock=SimulationClock(START, START),
        context=SimulationContext(id=uuid4(), community_id=uuid4(), community_profile_id=uuid4(), community_profile_version="1", community_map_id=uuid4(), community_map_version=1, scenario_id=SCENARIO_ID, scenario_version=1, primary_threat_id=uuid4(), available_resource_ids=(RESOURCE_ID,), participating_organization_ids=(uuid4(),), data_quality_score=80, created_at=START, checksum="checksum"),
    )
    definition = ScenarioDefinition(id=SCENARIO_ID, name="Impact", description="Impact scenario.", version=1, scenario_type=ScenarioType.TECHNOLOGICAL, difficulty=ScenarioDifficulty.MODERATE, initial_conditions=("initial",), simulation_goals=(ScenarioGoal(uuid4(), "goal"),), completion_criteria=("done",), initial_threat_ids=(uuid4(),), planned_events=(), allowed_team_roles=("coordinator",), metadata=ScenarioMetadata("TPS", "test"), phases=(ScenarioPhase("PRE_CRISIS"),), required_resource_ids=(RESOURCE_ID,), supported_threat_types=(ThreatType.TECHNOLOGICAL,))
    result.prepare(); result.load_scenario(definition); result.validate_scenario(("coordinator",)); result.activate_scenario(); result.start(); result.load_impact_engine()
    return result


def definition(change: ImpactChange, **overrides: object) -> ImpactDefinition:
    values: dict[str, object] = {"id": uuid4(), "scenario_id": SCENARIO_ID, "source_type": ImpactSourceType.SYSTEM, "source_id": SOURCE_ID, "name": "Generator use", "description": "Resource change.", "category": ImpactCategory.RESOURCE, "changes": (change,), "delay_minutes": 0, "duration_minutes": None, "temporary": False, "priority": 1, "conflict_policy": ImpactConflictPolicy.SEQUENTIAL}
    values.update(overrides)
    return ImpactDefinition(**values)  # type: ignore[arg-type]


def change(operation: ImpactOperation = ImpactOperation.INCREASE, value: float | bool = 2.0, **overrides: object) -> ImpactChange:
    values: dict[str, object] = {"target": ImpactTarget(ImpactTargetType.RESOURCE, RESOURCE_ID, "quantity"), "operation": operation, "value": value, "unit": "units", "minimum": 0.0}
    values.update(overrides)
    return ImpactChange(**values)  # type: ignore[arg-type]


def test_impact_definition_is_immutable() -> None:
    item = definition(change())
    with pytest.raises(FrozenInstanceError): item.name = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("operation", list(ImpactOperation))
def test_all_operations_have_typed_contract(operation: ImpactOperation) -> None:
    value: float | bool = True if operation in {ImpactOperation.ACTIVATE, ImpactOperation.DEACTIVATE, ImpactOperation.LOCK, ImpactOperation.UNLOCK} else 1.0
    assert change(operation, value).operation is operation


def test_resource_change_versions_only_runtime_state() -> None:
    simulation = sim(); key = StateKey(ImpactTargetType.RESOURCE, RESOURCE_ID, "quantity"); simulation.replace_simulation_state(SimulationState(simulation.id, 1, (StateValue(key, 10.0),)))
    item = simulation.create_impact(uuid4(), definition(change(ImpactOperation.DECREASE)), UUID(int=1)); result = simulation.apply_impact(item.id)
    assert simulation.state.get(key) == 8.0 and result.state_version_before == 1 and result.state_version_after == 2


def test_negative_values_are_rejected_atomically() -> None:
    simulation = sim(); key = StateKey(ImpactTargetType.RESOURCE, RESOURCE_ID, "quantity"); simulation.replace_simulation_state(SimulationState(simulation.id, 1, (StateValue(key, 1.0),)))
    item = simulation.create_impact(uuid4(), definition(change(ImpactOperation.DECREASE, value=2.0)), UUID(int=2))
    with pytest.raises(DomainRuleViolation): simulation.apply_impact(item.id)
    assert simulation.state.get(key) == 1.0 and item.status is ImpactStatus.FAILED


def test_delayed_impact_and_pause_guard() -> None:
    simulation = sim(); item = simulation.create_impact(uuid4(), definition(change(), delay_minutes=5), UUID(int=3))
    with pytest.raises(DomainRuleViolation): simulation.apply_impact(item.id)
    simulation.pause()
    with pytest.raises(DomainRuleViolation): simulation.refresh_impacts()
    simulation.resume(); simulation.advance_time(5); simulation.refresh_impacts()
    assert item.status is ImpactStatus.APPLIED


def test_temporary_additive_impact_reverses_once() -> None:
    simulation = sim(); key = StateKey(ImpactTargetType.RESOURCE, RESOURCE_ID, "quantity"); simulation.replace_simulation_state(SimulationState(simulation.id, 1, (StateValue(key, 5.0),)))
    item = simulation.create_impact(uuid4(), definition(change(ImpactOperation.INCREASE, 3.0), temporary=True, duration_minutes=5), UUID(int=4)); simulation.apply_impact(item.id)
    assert simulation.state.get(key) == 8.0 and item.status is ImpactStatus.ACTIVE
    simulation.advance_time(5); simulation.refresh_impacts(); assert simulation.state.get(key) == 5.0 and item.status is ImpactStatus.REVERSED
    with pytest.raises(DomainRuleViolation): simulation.reverse_impact(item.id)


def test_optional_failing_change_is_skipped() -> None:
    simulation = sim(); first = change(ImpactOperation.INCREASE, 1.0); optional = change(ImpactOperation.DECREASE, 2.0, required=False)
    item = simulation.create_impact(uuid4(), definition(first, changes=(first, optional)), UUID(int=5)); result = simulation.apply_impact(item.id)
    assert len(result.applied_changes) == 1 and len(result.skipped_changes) == 1


def test_conditions_and_final_instance_guard() -> None:
    simulation = sim(); item = simulation.create_impact(uuid4(), definition(change(), temporary=False), UUID(int=6)); simulation.apply_impact(item.id)
    with pytest.raises(DomainRuleViolation): simulation.apply_impact(item.id)


def test_two_simulations_have_isolated_state_and_deterministic_result() -> None:
    first = sim(); second = sim(); first_item = first.create_impact(UUID(int=100), definition(change(), id=UUID(int=101)), UUID(int=102)); first.apply_impact(first_item.id)
    assert first.state.version == 1 and second.state.version == 0