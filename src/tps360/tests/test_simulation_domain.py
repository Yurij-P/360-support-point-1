from datetime import datetime, timedelta
from uuid import UUID

import pytest

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    Scenario,
    Simulation,
    SimulationClock,
    SimulationContext,
    SimulationStatus,
    Timeline,
    TimelineEvent,
)
from tps360.threats.domain import Threat, ThreatSeverity, ThreatTargetType, ThreatType

START = datetime(2026, 7, 24, 9, 0)


def build_scenario(**overrides: object) -> Scenario:
    values: dict[str, object] = {
        "id": UUID("11111111-1111-1111-1111-111111111111"),
        "name": "Blackout response",
        "description": "Coordinate the response to an extended blackout.",
    }
    values.update(overrides)
    return Scenario(**values)  # type: ignore[arg-type]


def build_community() -> Community:
    return Community(name="Example", code="EX", oblast="Kyiv", population=1, area_km2=1.0)


def build_threat() -> Threat:
    return Threat(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        name="Power outage",
        threat_type=ThreatType.TECHNOLOGICAL,
        severity=ThreatSeverity.HIGH,
        target_type=ThreatTargetType.CRITICAL_INFRASTRUCTURE,
        description="Loss of electrical power.",
    )


def build_event(minutes: int = 10, **overrides: object) -> TimelineEvent:
    values: dict[str, object] = {
        "id": UUID("33333333-3333-3333-3333-333333333333"),
        "timestamp": START + timedelta(minutes=minutes),
        "name": "Power loss",
        "description": "Power loss is reported.",
    }
    values.update(overrides)
    return TimelineEvent(**values)  # type: ignore[arg-type]


def build_clock(**overrides: object) -> SimulationClock:
    values: dict[str, object] = {"start_time": START, "current_time": START}
    values.update(overrides)
    return SimulationClock(**values)  # type: ignore[arg-type]

def build_context() -> SimulationContext:
    return SimulationContext(
        id=UUID("66666666-6666-6666-6666-666666666666"),
        community_id=UUID("77777777-7777-7777-7777-777777777777"),
        community_profile_id=UUID("88888888-8888-8888-8888-888888888888"),
        community_profile_version="1.0.0",
        community_map_id=UUID("99999999-9999-9999-9999-999999999999"),
        community_map_version=1,
        scenario_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        scenario_version=1,
        primary_threat_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        participating_organization_ids=(UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),),
        data_quality_score=80.0,
        created_at=START,
        checksum="context-checksum",
    )

def build_simulation(**overrides: object) -> Simulation:
    clock = build_clock()
    values: dict[str, object] = {
        "id": UUID("44444444-4444-4444-4444-444444444444"),
        "scenario": build_scenario(),
        "community": build_community(),
        "threat": build_threat(),
        "timeline": Timeline(),
        "current_time": START,
        "status": SimulationStatus.DRAFT,
        "clock": clock,
        "context": build_context(),
    }
    values.update(overrides)
    return Simulation(**values)  # type: ignore[arg-type]


def test_valid_scenario() -> None:
    assert build_scenario().name == "Blackout response"


def test_empty_scenario_name_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_scenario(name=" ")


def test_empty_scenario_description_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_scenario(description=" ")


def test_valid_timeline_event() -> None:
    assert build_event().timestamp == START + timedelta(minutes=10)


def test_empty_event_name_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_event(name=" ")


def test_empty_event_description_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_event(description=" ")


def test_timeline_accepts_ordered_events() -> None:
    first = build_event(10)
    second = build_event(20, id=UUID("55555555-5555-5555-5555-555555555555"))

    assert Timeline((first, second)).events == (first, second)


def test_timeline_rejects_duplicate_event_ids() -> None:
    with pytest.raises(DomainRuleViolation):
        Timeline((build_event(10), build_event(20)))


def test_timeline_rejects_unordered_events() -> None:
    earlier = build_event(10)
    later = build_event(20, id=UUID("55555555-5555-5555-5555-555555555555"))

    with pytest.raises(DomainRuleViolation):
        Timeline((later, earlier))


def test_timeline_add_event_sorts_events() -> None:
    later = build_event(20)
    earlier = build_event(10, id=UUID("55555555-5555-5555-5555-555555555555"))

    assert Timeline((later,)).add_event(earlier).events == (earlier, later)


def test_timeline_add_event_rejects_duplicate_id() -> None:
    event = build_event()

    with pytest.raises(DomainRuleViolation):
        Timeline((event,)).add_event(event)


def test_timeline_events_until_returns_due_events() -> None:
    event = build_event()

    assert Timeline((event,)).events_until(event.timestamp) == (event,)


def test_valid_clock() -> None:
    assert build_clock().current_time == START


def test_clock_rejects_time_before_start() -> None:
    with pytest.raises(DomainRuleViolation):
        build_clock(current_time=START - timedelta(minutes=1))


def test_clock_advances_time() -> None:
    assert build_clock().advance(15).current_time == START + timedelta(minutes=15)


def test_clock_rejects_negative_advance() -> None:
    with pytest.raises(DomainRuleViolation):
        build_clock().advance(-1)


def test_clock_resets_time() -> None:
    clock = build_clock().advance(15)

    assert clock.reset().current_time == START

def test_valid_simulation() -> None:
    assert build_simulation().status is SimulationStatus.DRAFT


def test_simulation_requires_matching_clock_time() -> None:
    with pytest.raises(DomainRuleViolation):
        build_simulation(current_time=START + timedelta(minutes=1))


def test_simulation_starts() -> None:
    simulation = build_simulation()

    simulation.prepare()
    simulation.start()

    assert simulation.status is SimulationStatus.RUNNING

def test_only_draft_simulation_starts() -> None:
    with pytest.raises(DomainRuleViolation):
        build_simulation(status=SimulationStatus.RUNNING).start()


def test_running_simulation_pauses() -> None:
    simulation = build_simulation(status=SimulationStatus.RUNNING)

    simulation.pause()

    assert simulation.status is SimulationStatus.PAUSED


def test_only_running_simulation_pauses() -> None:
    with pytest.raises(DomainRuleViolation):
        build_simulation().pause()


def test_paused_simulation_resumes() -> None:
    simulation = build_simulation(status=SimulationStatus.PAUSED)

    simulation.resume()

    assert simulation.status is SimulationStatus.RUNNING


def test_only_paused_simulation_resumes() -> None:
    with pytest.raises(DomainRuleViolation):
        build_simulation().resume()


def test_simulation_completes() -> None:
    simulation = build_simulation()

    simulation.prepare()
    simulation.start()
    simulation.complete()

    assert simulation.status is SimulationStatus.COMPLETED

def test_completed_simulation_cannot_complete_again() -> None:
    with pytest.raises(DomainRuleViolation):
        build_simulation(status=SimulationStatus.COMPLETED).complete()


def test_running_simulation_advances_time() -> None:
    simulation = build_simulation(status=SimulationStatus.RUNNING)

    assert simulation.advance_time(5) == ()
    assert simulation.current_time == START + timedelta(minutes=5)


def test_only_running_simulation_advances_time() -> None:
    with pytest.raises(DomainRuleViolation):
        build_simulation().advance_time(5)


def test_advancing_simulation_returns_due_events() -> None:
    event = build_event()
    simulation = build_simulation(
        timeline=Timeline((event,)),
        status=SimulationStatus.RUNNING,
    )

    assert simulation.advance_time(10) == (event,)