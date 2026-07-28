from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    ApprovalRule,
    DecisionApproval,
    DecisionOption,
    DecisionParticipationPolicy,
    DecisionPriority,
    DecisionRequest,
    DecisionRequestStatus,
    DecisionSubmission,
    DecisionSubmissionStatus,
    DecisionType,
    EventPriority,
    EventRuntimeStatus,
    ResourceAllocation,
    Scenario,
    ScenarioDefinition,
    ScenarioDifficulty,
    ScenarioGoal,
    ScenarioMetadata,
    ScenarioPhase,
    ScenarioType,
    ScheduledEvent,
    ScheduledEventType,
    SchedulerState,
    Simulation,
    SimulationClock,
    SimulationContext,
    SimulationStatus,
    Timeline,
)
from tps360.threats.domain import Threat, ThreatSeverity, ThreatTargetType, ThreatType

START = datetime(2026, 7, 24, 9, 0)
SCENARIO_ID = UUID("22222222-2222-2222-2222-222222222222")
RESOURCE_ID = UUID("11111111-1111-1111-1111-111111111111")
TEAM_ID = UUID("44444444-4444-4444-4444-444444444444")
ROLE_ID = UUID("55555555-5555-5555-5555-555555555555")
APPROVER_ID = UUID("66666666-6666-6666-6666-666666666666")


def policy(**overrides: object) -> DecisionParticipationPolicy:
    values: dict[str, object] = {"permitted_team_ids": (TEAM_ID,), "permitted_role_ids": (ROLE_ID,), "approval_role_ids": (), "minimum_quorum": 1}
    values.update(overrides)
    return DecisionParticipationPolicy(**values)  # type: ignore[arg-type]


def request(**overrides: object) -> DecisionRequest:
    values: dict[str, object] = {
        "id": uuid4(), "simulation_id": UUID(int=0), "scenario_id": SCENARIO_ID, "related_event_id": None,
        "name": "Evacuate district", "description": "Select the response.", "decision_type": DecisionType.SINGLE_CHOICE,
        "priority": DecisionPriority.HIGH, "created_at": START, "deadline": START + timedelta(minutes=30),
        "allowed_role_ids": (ROLE_ID,), "options": (DecisionOption("evacuate", "Evacuate"), DecisionOption("shelter", "Shelter in place")),
        "allow_free_text": True, "justification_required": True, "participation_policy": policy(),
        "resource_limits": (ResourceAllocation(RESOURCE_ID, 10),), "metadata": (("source", "test"),), "version": 1,
    }
    values.update(overrides)
    return DecisionRequest(**values)  # type: ignore[arg-type]


def submission(req: DecisionRequest, **overrides: object) -> DecisionSubmission:
    values: dict[str, object] = {
        "id": uuid4(), "request_id": req.id, "team_id": TEAM_ID, "role_id": ROLE_ID,
        "selected_option_ids": ("evacuate",), "justification": "Protect residents.", "resource_allocations": (),
        "confidence": 80, "submitted_at": START + timedelta(minutes=1), "version": 1,
    }
    values.update(overrides)
    return DecisionSubmission(**values)  # type: ignore[arg-type]


def definition(events: tuple[ScheduledEvent, ...] = ()) -> ScenarioDefinition:
    return ScenarioDefinition(
        id=SCENARIO_ID, name="Decision scenario", description="Coordinate response.", version=1,
        scenario_type=ScenarioType.TECHNOLOGICAL, difficulty=ScenarioDifficulty.MODERATE,
        initial_conditions=("Power lost",), simulation_goals=(ScenarioGoal(uuid4(), "Protect people"),),
        completion_criteria=("protected",), initial_threat_ids=(uuid4(),), planned_events=(), allowed_team_roles=("coordinator",),
        metadata=ScenarioMetadata("TPS360", "test"), phases=(ScenarioPhase("PRE_CRISIS"),),
        required_resource_ids=(RESOURCE_ID,), supported_threat_types=(ThreatType.TECHNOLOGICAL,), scheduled_events=events,
    )


def simulation(events: tuple[ScheduledEvent, ...] = ()) -> Simulation:
    result = Simulation(
        id=uuid4(), scenario=Scenario(uuid4(), "Session", "Decision session."),
        community=Community(name="Example", code="EX", oblast="Kyiv", population=1, area_km2=1.0),
        threat=Threat(uuid4(), "Power loss", ThreatType.TECHNOLOGICAL, ThreatSeverity.HIGH, ThreatTargetType.CRITICAL_INFRASTRUCTURE, "Power loss."),
        timeline=Timeline(), current_time=START, status=SimulationStatus.DRAFT,
        clock=SimulationClock(START, START),
        context=SimulationContext(id=uuid4(), community_id=str(uuid4()), community_profile_id=uuid4(), community_profile_version="1", community_map_id=uuid4(), community_map_version=1, scenario_id=SCENARIO_ID, scenario_version=1, primary_threat_id=uuid4(), available_resource_ids=(RESOURCE_ID,), participating_organization_ids=(uuid4(),), data_quality_score=80, created_at=START, checksum="checksum"),
    )
    result.prepare(); result.load_scenario(definition(events)); result.validate_scenario(("coordinator",)); result.activate_scenario(); result.start(); result.load_decision_engine()
    return result


@pytest.mark.parametrize("kind", list(DecisionType))
def test_creates_all_decision_request_types(kind: DecisionType) -> None:
    sim = simulation()
    req = request(simulation_id=sim.id, decision_type=kind, options=() if kind in {DecisionType.FREE_TEXT, DecisionType.RESOURCE_ALLOCATION, DecisionType.APPROVAL, DecisionType.COORDINATED} else request().options)
    runtime = sim.create_decision_request(req)
    assert runtime.status is DecisionRequestStatus.DRAFT


def test_request_is_immutable() -> None:
    item = request()
    with pytest.raises(FrozenInstanceError):
        item.name = "Changed"  # type: ignore[misc]


def test_open_and_submit_valid_single_choice() -> None:
    sim = simulation(); req = request(simulation_id=sim.id); sim.create_decision_request(req); sim.open_decision_request(req.id); sim.submit_decision(submission(req))
    assert sim.decision_engine is not None and sim.decision_engine.runtimes[0].submissions[0].status is DecisionSubmissionStatus.VALID


def test_paused_simulation_rejects_submission() -> None:
    sim = simulation(); req = request(simulation_id=sim.id); sim.create_decision_request(req); sim.open_decision_request(req.id); sim.pause()
    with pytest.raises(DomainRuleViolation): sim.submit_decision(submission(req))


def test_deadline_rejects_submission() -> None:
    sim = simulation(); req = request(simulation_id=sim.id, deadline=START); sim.create_decision_request(req); sim.open_decision_request(req.id); sim.advance_time(1)
    with pytest.raises(DomainRuleViolation): sim.submit_decision(submission(req, submitted_at=sim.current_time))


def test_role_team_and_justification_validation() -> None:
    sim = simulation(); req = request(simulation_id=sim.id); sim.create_decision_request(req); sim.open_decision_request(req.id)
    with pytest.raises(DomainRuleViolation): sim.submit_decision(submission(req, role_id=uuid4()))
    with pytest.raises(DomainRuleViolation): sim.submit_decision(submission(req, justification="  "))


def test_option_resource_and_duplicate_submission_validation() -> None:
    sim = simulation(); req = request(simulation_id=sim.id); sim.create_decision_request(req); sim.open_decision_request(req.id)
    with pytest.raises(DomainRuleViolation): sim.submit_decision(submission(req, selected_option_ids=("unknown",)))
    with pytest.raises(DomainRuleViolation): sim.submit_decision(submission(req, resource_allocations=(ResourceAllocation(RESOURCE_ID, 11),)))
    sim.submit_decision(submission(req))
    with pytest.raises(DomainRuleViolation): sim.submit_decision(submission(req))


def test_withdrawal_only_before_review() -> None:
    sim = simulation(); req = request(simulation_id=sim.id); sim.create_decision_request(req); sim.open_decision_request(req.id); item = submission(req); sim.submit_decision(item); sim.decision_engine.withdraw(req.id, item.id, sim.current_time); assert item.status is DecisionSubmissionStatus.WITHDRAWN
    sim.start_decision_review(req.id)
    with pytest.raises(DomainRuleViolation): sim.decision_engine.withdraw(req.id, item.id, sim.current_time)


def test_all_approval_and_quorum_create_deterministic_outcome() -> None:
    p = policy(approval_role_ids=(APPROVER_ID,), minimum_quorum=1)
    sim = simulation(); req = request(simulation_id=sim.id, participation_policy=p, allowed_role_ids=(ROLE_ID,))
    sim.create_decision_request(req); sim.open_decision_request(req.id); sim.submit_decision(submission(req)); sim.decision_engine.record_approval(req.id, DecisionApproval(APPROVER_ID, True, "Approved", sim.current_time))
    outcome = sim.approve_decision(req.id, "Proceed", UUID(int=9))
    assert outcome.accepted_option_ids == ("evacuate",) and sim.decision_engine.runtimes[0].status is DecisionRequestStatus.APPROVED


def test_any_approval_and_conflict_readiness() -> None:
    p = policy(permitted_role_ids=(ROLE_ID, APPROVER_ID), approval_role_ids=(APPROVER_ID, ROLE_ID), approval_rule=ApprovalRule.ANY, minimum_quorum=0)
    sim = simulation(); req = request(simulation_id=sim.id, participation_policy=p, allowed_role_ids=(ROLE_ID, APPROVER_ID), decision_type=DecisionType.COORDINATED)
    sim.create_decision_request(req); sim.open_decision_request(req.id); sim.decision_engine.record_approval(req.id, DecisionApproval(APPROVER_ID, True, "yes", sim.current_time))
    assert sim.decision_engine.readiness(req.id).ready


def test_rejection_duplicate_vote_and_execution_lifecycle() -> None:
    p = policy(approval_role_ids=(APPROVER_ID,), minimum_quorum=0); sim = simulation(); req = request(simulation_id=sim.id, participation_policy=p); sim.create_decision_request(req); sim.open_decision_request(req.id)
    sim.decision_engine.record_approval(req.id, DecisionApproval(APPROVER_ID, False, "no", sim.current_time))
    with pytest.raises(DomainRuleViolation): sim.decision_engine.record_approval(req.id, DecisionApproval(APPROVER_ID, True, "again", sim.current_time))
    sim.decision_engine.reject(req.id, sim.current_time, "no")
    with pytest.raises(DomainRuleViolation): sim.decision_engine.execute(req.id, sim.current_time)


def test_approved_execution_expiry_cancellation_and_final_guard() -> None:
    p = policy(minimum_quorum=0); sim = simulation(); req = request(simulation_id=sim.id, participation_policy=p); sim.create_decision_request(req); sim.open_decision_request(req.id); sim.submit_decision(submission(req)); sim.approve_decision(req.id, "go", UUID(int=1)); sim.decision_engine.execute(req.id, sim.current_time)
    with pytest.raises(DomainRuleViolation): sim.decision_engine.cancel(req.id, sim.current_time)
    other = request(id=uuid4(), simulation_id=sim.id, participation_policy=p, deadline=START); sim.create_decision_request(other); sim.open_decision_request(other.id); sim.advance_time(1); sim.decision_engine.expire(other.id, sim.current_time)
    assert sim.decision_engine.runtimes[1].status is DecisionRequestStatus.EXPIRED


def test_active_event_integration_and_foreign_event_rejection() -> None:
    event = ScheduledEvent(uuid4(), SCENARIO_ID, "Inject", "Decision needed", ScheduledEventType.TIME_BASED, EventPriority.HIGH, "PRE_CRISIS", START, (), (), ApprovalRule.ALL, (), (), (), (), (), True, 0, None, ScenarioMetadata("TPS", "test"), 1)
    sim = simulation((event,)); sim.load_event_scheduler(); sim.refresh_scheduled_events(SchedulerState())
    assert sim.event_scheduler is not None and sim.event_scheduler.event_runtimes[0].status is EventRuntimeStatus.ACTIVE
    req = request(simulation_id=sim.id, related_event_id=event.id); sim.create_decision_request(req)
    with pytest.raises(DomainRuleViolation): sim.create_decision_request(request(id=uuid4(), simulation_id=sim.id, related_event_id=uuid4()))


def test_two_sessions_are_isolated_and_events_are_audited() -> None:
    first = simulation(); second = simulation(); req = request(simulation_id=first.id); first.create_decision_request(req); first.open_decision_request(req.id); first.submit_decision(submission(req))
    assert second.decision_engine is not None and not second.decision_engine.runtimes
    assert first.decision_engine is not None and len(first.decision_engine.audit_trail) >= 3