from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    Scenario,
    Simulation,
    SimulationCancelled,
    SimulationClock,
    SimulationCompleted,
    SimulationContext,
    SimulationPaused,
    SimulationPrepared,
    SimulationResumed,
    SimulationStarted,
    SimulationStatus,
    SimulationTimeAdvanced,
    Timeline,
)
from tps360.threats.domain import Threat, ThreatSeverity, ThreatTargetType, ThreatType

START = datetime(2026, 7, 24, 9, 0)


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
        participating_organization_ids=(uuid4(),),
        data_quality_score=80.0,
        created_at=START,
        checksum="checksum",
    )


def build_simulation(**overrides: object) -> Simulation:
    clock = SimulationClock(start_time=START, current_time=START)
    values: dict[str, object] = {
        "id": uuid4(),
        "scenario": Scenario(id=uuid4(), name="Exercise", description="Lifecycle exercise."),
        "community": Community(name="Example", code="EX", oblast="Kyiv", population=1, area_km2=1.0),
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
        "clock": clock,
        "context": build_context(),
    }
    values.update(overrides)
    return Simulation(**values)  # type: ignore[arg-type]


def start_simulation(simulation: Simulation) -> Simulation:
    simulation.prepare()
    simulation.start()
    return simulation


def test_draft_transitions_to_ready_with_event_and_audit_record() -> None:
    simulation = build_simulation()

    simulation.prepare()

    assert simulation.status is SimulationStatus.READY
    assert isinstance(simulation.domain_events[-1], SimulationPrepared)
    assert simulation.audit_trail == simulation.domain_events


def test_only_draft_session_can_be_prepared() -> None:
    simulation = build_simulation(status=SimulationStatus.READY)

    with pytest.raises(DomainRuleViolation):
        simulation.prepare()


def test_ready_transitions_to_running_with_started_event() -> None:
    simulation = build_simulation()
    simulation.prepare()

    simulation.start()

    assert simulation.status is SimulationStatus.RUNNING
    assert isinstance(simulation.audit_trail[-1], SimulationStarted)


def test_draft_session_cannot_start() -> None:
    with pytest.raises(DomainRuleViolation):
        build_simulation().start()


def test_running_transitions_to_paused_with_event() -> None:
    simulation = start_simulation(build_simulation())

    simulation.pause()

    assert simulation.status is SimulationStatus.PAUSED
    assert isinstance(simulation.audit_trail[-1], SimulationPaused)


def test_paused_transitions_to_running_with_resumed_event() -> None:
    simulation = start_simulation(build_simulation())
    simulation.pause()

    simulation.resume()

    assert simulation.status is SimulationStatus.RUNNING
    assert isinstance(simulation.audit_trail[-1], SimulationResumed)


def test_running_session_can_complete_with_event() -> None:
    simulation = start_simulation(build_simulation())

    simulation.complete()

    assert simulation.status is SimulationStatus.COMPLETED
    assert isinstance(simulation.audit_trail[-1], SimulationCompleted)


def test_paused_session_can_complete() -> None:
    simulation = start_simulation(build_simulation())
    simulation.pause()

    simulation.complete()

    assert simulation.status is SimulationStatus.COMPLETED


@pytest.mark.parametrize(
    "status",
    [SimulationStatus.DRAFT, SimulationStatus.READY, SimulationStatus.RUNNING, SimulationStatus.PAUSED],
)
def test_every_unfinished_session_can_be_cancelled(status: SimulationStatus) -> None:
    simulation = build_simulation(status=status)

    simulation.cancel()

    assert simulation.status is SimulationStatus.CANCELLED
    assert isinstance(simulation.audit_trail[-1], SimulationCancelled)


@pytest.mark.parametrize("method_name", ["pause", "resume", "complete"])
def test_draft_session_rejects_disallowed_transitions(method_name: str) -> None:
    simulation = build_simulation()

    with pytest.raises(DomainRuleViolation):
        getattr(simulation, method_name)()


def test_clock_is_immutable() -> None:
    clock = SimulationClock(start_time=START, current_time=START)

    with pytest.raises(FrozenInstanceError):
        clock.current_time = START + timedelta(minutes=1)  # type: ignore[misc]


def test_clock_advances_with_acceleration_factor() -> None:
    clock = SimulationClock(start_time=START, current_time=START, acceleration_factor=3.0)

    advanced_clock = clock.advance(5)

    assert advanced_clock.current_time == START + timedelta(minutes=15)
    assert clock.current_time == START


def test_clock_never_moves_backwards() -> None:
    with pytest.raises(DomainRuleViolation):
        SimulationClock(start_time=START, current_time=START - timedelta(minutes=1))


def test_clock_is_deterministic_without_system_time() -> None:
    first = SimulationClock(start_time=START, current_time=START, acceleration_factor=2.0).advance(7)
    second = SimulationClock(start_time=START, current_time=START, acceleration_factor=2.0).advance(7)

    assert first == second


def test_time_moves_only_while_running() -> None:
    simulation = start_simulation(build_simulation())
    simulation.pause()

    with pytest.raises(DomainRuleViolation):
        simulation.advance_time(1)


def test_time_advance_creates_event_and_updates_clock() -> None:
    simulation = start_simulation(build_simulation())

    simulation.advance_time(4)

    event = simulation.audit_trail[-1]
    assert simulation.current_time == START + timedelta(minutes=4)
    assert isinstance(event, SimulationTimeAdvanced)
    assert event.elapsed_simulation_minutes == 4.0


def test_completed_session_cannot_be_changed() -> None:
    simulation = start_simulation(build_simulation())
    simulation.complete()

    with pytest.raises(DomainRuleViolation):
        simulation.advance_time(1)
    with pytest.raises(DomainRuleViolation):
        simulation.status = SimulationStatus.RUNNING


def test_cancelled_session_cannot_restart() -> None:
    simulation = build_simulation()
    simulation.cancel()

    with pytest.raises(DomainRuleViolation):
        simulation.prepare()


def test_context_cannot_be_replaced_after_start() -> None:
    simulation = start_simulation(build_simulation())

    with pytest.raises(DomainRuleViolation):
        simulation.context = build_context()


def test_base_community_remains_unchanged() -> None:
    simulation = start_simulation(build_simulation())
    original_community = simulation.community.model_dump()

    simulation.advance_time(10)
    simulation.pause()
    simulation.complete()

    assert simulation.community.model_dump() == original_community


def test_parallel_simulations_have_isolated_state() -> None:
    first = start_simulation(build_simulation())
    second = start_simulation(build_simulation())

    first.advance_time(10)

    assert first.current_time == START + timedelta(minutes=10)
    assert second.current_time == START
    assert first.audit_trail != second.audit_trail