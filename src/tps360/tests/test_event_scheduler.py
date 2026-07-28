from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    ActivationCondition,
    ActivationConditionType,
    DependencyRule,
    EventDependency,
    EventParameter,
    EventPriority,
    EventRuntimeStatus,
    Scenario,
    ScenarioDefinition,
    ScenarioDifficulty,
    ScenarioGoal,
    ScenarioMetadata,
    ScenarioPhase,
    ScenarioType,
    ScheduledEvent,
    ScheduledEventType,
    Simulation,
    SimulationClock,
    SimulationContext,
    SimulationStatus,
    Timeline,
)
from tps360.simulation.domain.event_scheduler import EventScheduler, SchedulerState
from tps360.threats.domain import Threat, ThreatSeverity, ThreatTargetType, ThreatType

START = datetime(2026, 7, 24, 9, 0)
RESOURCE_ID = UUID("11111111-1111-1111-1111-111111111111")
SCENARIO_ID = UUID("22222222-2222-2222-2222-222222222222")


def build_event(**overrides: object) -> ScheduledEvent:
    values: dict[str, object] = {
        "id": UUID("33333333-3333-3333-3333-333333333333"),
        "scenario_id": SCENARIO_ID,
        "name": "Power loss",
        "description": "Power is lost in the central district.",
        "event_type": ScheduledEventType.TIME_BASED,
        "priority": EventPriority.HIGH,
        "scenario_phase": "PRE_CRISIS",
        "scheduled_time": START + timedelta(minutes=10),
        "activation_conditions": (),
        "dependencies": (),
        "dependency_rule": DependencyRule.ALL,
        "target_territories": (),
        "target_infrastructure": (),
        "target_resource_ids": (),
        "target_population_groups": (),
        "parameters": (),
        "mandatory": True,
        "repeat_count": 0,
        "recurrence_interval_minutes": None,
        "metadata": ScenarioMetadata(author="TPS360", source="exercise"),
        "version": 1,
    }
    values.update(overrides)
    return ScheduledEvent(**values)  # type: ignore[arg-type]


def build_definition(events: tuple[ScheduledEvent, ...]) -> ScenarioDefinition:
    return ScenarioDefinition(
        id=SCENARIO_ID,
        name="Power outage response",
        description="Coordinate response.",
        version=1,
        scenario_type=ScenarioType.TECHNOLOGICAL,
        difficulty=ScenarioDifficulty.MODERATE,
        initial_conditions=("Power unavailable.",),
        simulation_goals=(ScenarioGoal(uuid4(), "Restore power."),),
        completion_criteria=("power_restored",),
        initial_threat_ids=(uuid4(),),
        planned_events=(),
        allowed_team_roles=("coordinator",),
        metadata=ScenarioMetadata(author="TPS360", source="exercise"),
        phases=(ScenarioPhase("PRE_CRISIS"), ScenarioPhase("ESCALATION")),
        required_resource_ids=(RESOURCE_ID,),
        supported_threat_types=(ThreatType.TECHNOLOGICAL,),
        scheduled_events=events,
    )


def build_simulation() -> Simulation:
    return Simulation(
        id=uuid4(),
        scenario=Scenario(
            id=uuid4(), name="Session", description="Scheduler session."
        ),
        community=Community(name="Example", code="EX", oblast="Kyiv", population=1, area_km2=1.0),
        threat=Threat(
            id=uuid4(),
            name="Power outage",
            threat_type=ThreatType.TECHNOLOGICAL,
            severity=ThreatSeverity.HIGH,
            target_type=ThreatTargetType.CRITICAL_INFRASTRUCTURE,
            description="Loss of electrical power.",
        ),
        timeline=Timeline(),
        current_time=START,
        status=SimulationStatus.DRAFT,
        clock=SimulationClock(start_time=START, current_time=START),
        context=SimulationContext(
            id=uuid4(),
            community_id=str(uuid4()),
            community_profile_id=uuid4(),
            community_profile_version="1.0.0",
            community_map_id=uuid4(),
            community_map_version=1,
            scenario_id=SCENARIO_ID,
            scenario_version=1,
            primary_threat_id=uuid4(),
            available_resource_ids=(RESOURCE_ID,),
            participating_organization_ids=(uuid4(),),
            data_quality_score=80.0,
            created_at=START,
            checksum="checksum",
        ),
    )


def active_scheduler(events: tuple[ScheduledEvent, ...]) -> Simulation:
    simulation = build_simulation()
    simulation.prepare()
    simulation.load_scenario(build_definition(events))
    simulation.validate_scenario(("coordinator",))
    simulation.activate_scenario()
    simulation.start()
    simulation.load_event_scheduler()
    return simulation


@pytest.mark.parametrize(
    "event_type",
    [
        ScheduledEventType.TIME_BASED,
        ScheduledEventType.CONDITION_BASED,
        ScheduledEventType.DEPENDENCY_BASED,
        ScheduledEventType.MANUAL,
        ScheduledEventType.RECURRING,
    ],
)
def test_scheduler_loads_all_event_types(event_type: ScheduledEventType) -> None:
    event = build_event(
        event_type=event_type,
        scheduled_time=START + timedelta(minutes=10)
        if event_type in {ScheduledEventType.TIME_BASED, ScheduledEventType.RECURRING}
        else None,
        recurrence_interval_minutes=5 if event_type is ScheduledEventType.RECURRING else None,
    )

    scheduler = EventScheduler.load(uuid4(), SCENARIO_ID, (event,), START)

    assert scheduler.event_runtimes[0].definition.event_type is event_type


def test_time_based_event_activates_after_clock_advance() -> None:
    event = build_event()
    simulation = active_scheduler((event,))

    simulation.advance_time(10)

    assert simulation.event_scheduler is not None
    assert simulation.event_scheduler.event_runtimes[0].status is EventRuntimeStatus.ACTIVE


def test_event_does_not_activate_early() -> None:
    simulation = active_scheduler((build_event(),))

    simulation.refresh_scheduled_events(SchedulerState())

    assert simulation.event_scheduler is not None
    assert simulation.event_scheduler.event_runtimes[0].status is EventRuntimeStatus.BLOCKED


def test_events_do_not_activate_while_simulation_is_paused() -> None:
    simulation = active_scheduler((build_event(scheduled_time=START),))
    simulation.pause()

    with pytest.raises(DomainRuleViolation):
        simulation.refresh_scheduled_events(SchedulerState())


def test_manual_event_activates_only_through_manual_method() -> None:
    event = build_event(event_type=ScheduledEventType.MANUAL, scheduled_time=None)
    simulation = active_scheduler((event,))

    simulation.manually_activate_event(event.id, SchedulerState())

    assert simulation.event_scheduler is not None
    assert simulation.event_scheduler.event_runtimes[0].status is EventRuntimeStatus.ACTIVE


def test_non_manual_event_cannot_be_manually_activated() -> None:
    event = build_event()
    simulation = active_scheduler((event,))

    with pytest.raises(DomainRuleViolation):
        simulation.manually_activate_event(event.id, SchedulerState())


def test_state_value_activation_condition() -> None:
    event = build_event(
        event_type=ScheduledEventType.CONDITION_BASED,
        scheduled_time=None,
        activation_conditions=(
            ActivationCondition(
                ActivationConditionType.STATE_VALUE_EQUALS,
                key="water_level",
                expected_value=3,
            ),
        ),
    )
    simulation = active_scheduler((event,))

    simulation.refresh_scheduled_events(SchedulerState((EventParameter("water_level", 3),)))

    assert simulation.event_scheduler is not None
    assert simulation.event_scheduler.event_runtimes[0].status is EventRuntimeStatus.ACTIVE


def test_all_dependencies_must_resolve() -> None:
    first = build_event(id=UUID("44444444-4444-4444-4444-444444444444"), scheduled_time=START)
    second = build_event(
        id=UUID("55555555-5555-5555-5555-555555555555"),
        scheduled_time=START,
        dependencies=(EventDependency(first.id),),
    )
    simulation = active_scheduler((first, second))
    simulation.refresh_scheduled_events(SchedulerState())

    assert simulation.event_scheduler is not None
    assert simulation.event_scheduler.event_runtimes[1].status is EventRuntimeStatus.BLOCKED
    simulation.resolve_scheduled_event(first.id)
    simulation.refresh_scheduled_events(SchedulerState())
    assert simulation.event_scheduler.event_runtimes[1].status is EventRuntimeStatus.ACTIVE


def test_any_dependencies_allow_one_resolved_event() -> None:
    first = build_event(id=UUID("44444444-4444-4444-4444-444444444444"), scheduled_time=START)
    second = build_event(id=UUID("55555555-5555-5555-5555-555555555555"), scheduled_time=START)
    dependent = build_event(
        id=UUID("66666666-6666-6666-6666-666666666666"),
        scheduled_time=START,
        dependencies=(EventDependency(first.id), EventDependency(second.id)),
        dependency_rule=DependencyRule.ANY,
    )
    simulation = active_scheduler((first, second, dependent))
    simulation.refresh_scheduled_events(SchedulerState())
    simulation.resolve_scheduled_event(first.id)
    simulation.refresh_scheduled_events(SchedulerState())

    assert simulation.event_scheduler is not None
    assert next(runtime for runtime in simulation.event_scheduler.event_runtimes if runtime.definition.id == dependent.id).status is EventRuntimeStatus.ACTIVE


def test_optional_missing_dependency_is_warning_not_blocker() -> None:
    event = build_event(dependencies=(EventDependency(uuid4(), required=False),))

    scheduler = EventScheduler.load(uuid4(), SCENARIO_ID, (event,), START)

    assert scheduler.validation_result.warnings


def test_self_dependency_blocks_schedule_loading() -> None:
    event = build_event()
    event = build_event(dependencies=(EventDependency(event.id),))

    with pytest.raises(DomainRuleViolation):
        EventScheduler.load(uuid4(), SCENARIO_ID, (event,), START)


def test_cyclic_dependencies_block_schedule_loading() -> None:
    first_id = UUID("44444444-4444-4444-4444-444444444444")
    second_id = UUID("55555555-5555-5555-5555-555555555555")
    first = build_event(id=first_id, dependencies=(EventDependency(second_id),))
    second = build_event(id=second_id, dependencies=(EventDependency(first_id),))

    with pytest.raises(DomainRuleViolation):
        EventScheduler.load(uuid4(), SCENARIO_ID, (first, second), START)


def test_same_time_events_use_priority_then_stable_id_order() -> None:
    low = build_event(id=UUID("99999999-9999-9999-9999-999999999999"), scheduled_time=START, priority=EventPriority.LOW)
    high = build_event(id=UUID("11111111-1111-1111-1111-111111111111"), scheduled_time=START, priority=EventPriority.HIGH)
    scheduler = EventScheduler.load(uuid4(), SCENARIO_ID, (low, high), START)

    assert tuple(runtime.definition.id for runtime in scheduler.event_runtimes) == (high.id, low.id)


def test_recurring_event_creates_separate_occurrence() -> None:
    event = build_event(
        event_type=ScheduledEventType.RECURRING,
        scheduled_time=START,
        repeat_count=1,
        recurrence_interval_minutes=5,
    )
    simulation = active_scheduler((event,))
    simulation.refresh_scheduled_events(SchedulerState())

    next_occurrence = simulation.resolve_scheduled_event(event.id)

    assert next_occurrence is not None
    assert next_occurrence.occurrence_index == 1
    assert next_occurrence.scheduled_time == START + timedelta(minutes=5)


def test_event_lifecycle_resolve_fail_cancel_and_expire() -> None:
    resolved = build_event(id=UUID("44444444-4444-4444-4444-444444444444"), scheduled_time=START)
    failed = build_event(id=UUID("55555555-5555-5555-5555-555555555555"), scheduled_time=START)
    cancelled = build_event(id=UUID("66666666-6666-6666-6666-666666666666"), scheduled_time=START)
    expired = build_event(id=UUID("77777777-7777-7777-7777-777777777777"), scheduled_time=START, scenario_phase="ESCALATION", expires_at=START + timedelta(minutes=5))
    simulation = active_scheduler((resolved, failed, cancelled, expired))
    simulation.refresh_scheduled_events(SchedulerState())
    simulation.resolve_scheduled_event(resolved.id)
    simulation.fail_scheduled_event(failed.id)
    simulation.cancel_scheduled_event(cancelled.id)
    simulation.advance_time(6)

    assert simulation.event_scheduler is not None
    statuses = {runtime.definition.id: runtime.status for runtime in simulation.event_scheduler.event_runtimes}
    assert statuses[resolved.id] is EventRuntimeStatus.RESOLVED
    assert statuses[failed.id] is EventRuntimeStatus.FAILED
    assert statuses[cancelled.id] is EventRuntimeStatus.CANCELLED
    assert statuses[expired.id] is EventRuntimeStatus.EXPIRED


def test_final_event_cannot_change() -> None:
    event = build_event(scheduled_time=START)
    simulation = active_scheduler((event,))
    simulation.refresh_scheduled_events(SchedulerState())
    simulation.resolve_scheduled_event(event.id)

    with pytest.raises(DomainRuleViolation):
        simulation.cancel_scheduled_event(event.id)


def test_scheduler_events_and_audit_trail_are_recorded() -> None:
    event = build_event(scheduled_time=START)
    simulation = active_scheduler((event,))
    simulation.refresh_scheduled_events(SchedulerState())

    assert simulation.event_scheduler is not None
    assert simulation.event_scheduler.audit_trail
    assert simulation.event_scheduler.audit_trail[-1].occurred_at == START


def test_schedulers_are_isolated_for_parallel_simulations() -> None:
    event = build_event()
    first = active_scheduler((event,))
    second = active_scheduler((event,))
    first.advance_time(10)

    assert first.event_scheduler is not None
    assert second.event_scheduler is not None
    assert first.event_scheduler is not second.event_scheduler
    assert second.event_scheduler.event_runtimes[0].status is EventRuntimeStatus.SCHEDULED


def test_scheduler_is_deterministic_and_definition_is_unchanged() -> None:
    event = build_event(scheduled_time=START)
    definition = build_definition((event,))
    first = active_scheduler((event,))
    second = active_scheduler((event,))
    first.refresh_scheduled_events(SchedulerState())
    second.refresh_scheduled_events(SchedulerState())

    assert first.event_scheduler is not None
    assert second.event_scheduler is not None
    assert first.event_scheduler.event_runtimes[0].status == second.event_scheduler.event_runtimes[0].status
    assert definition.scheduled_events == (event,)


def test_scheduler_does_not_mutate_community_snapshot() -> None:
    event = build_event(scheduled_time=START)
    simulation = active_scheduler((event,))
    original = simulation.community.model_dump()

    simulation.refresh_scheduled_events(SchedulerState())

    assert simulation.community.model_dump() == original