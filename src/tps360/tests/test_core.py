from datetime import date
from uuid import uuid4
import pytest
from tps360.core.domain.enums import HazardCategory, LifecycleStatus
from tps360.core.domain.models import Community, Decision, Evaluation, Hazard, ImprovementPlan, Inject, Risk
from tps360.core.exceptions import DomainRuleViolation
from tps360.core.services import EvaluationService, ImprovementService, PreparednessService, RiskService, SimulationService
from tps360.core.value_objects import Score

@pytest.mark.parametrize("value", [-1, 101, 200])
def test_score_rejects_bounds(value):
    with pytest.raises(ValueError): Score(value, "TPS")

@pytest.mark.parametrize("population", [0, 1, 1000])
def test_community_valid(population):
    assert Community(name="A", code=str(population), oblast="O", population=population, area_km2=1).population == population

def test_community_rejects_negative_population():
    with pytest.raises(ValueError): Community(name="A", code="x", oblast="O", population=-1, area_km2=1)

@pytest.mark.parametrize("score,level", [(0,"reactive"),(20,"basic"),(40,"managed"),(60,"integrated"),(80,"resilient")])
def test_cpmm(score, level): assert PreparednessService().determine_maturity_level(score).value == level

def test_risk_calculation_is_explicit():
    risk=Risk(community_id=uuid4(),hazard=Hazard(name="H",category=HazardCategory.NATURAL,description="d",probability=50,potential_impact=50,geographic_scope="g"),probability_score=50,impact_score=50,exposure_score=50,capability_modifier=0,confidence_level="medium",evidence=["e"])
    assert risk.overall_score is None and RiskService().calculate_risk(risk)==50

def test_simulation_lifecycle_and_decision():
    svc=SimulationService(); sim=svc.create_simulation(uuid4(),uuid4()); svc.start_simulation(sim); assert sim.status is LifecycleStatus.ACTIVE
    svc.record_decision(sim,Decision(simulation_id=sim.id,actor="a",description="d",rationale="r",selected_action="x")); assert len(sim.decisions)==1
    svc.complete_simulation(sim); assert sim.status is LifecycleStatus.COMPLETED

def test_inject_delivery_requires_active():
    svc=SimulationService(); sim=svc.create_simulation(uuid4(),uuid4()); inject=Inject(scenario_id=sim.scenario_id,sequence=1,scheduled_offset_minutes=0,title="i",description="d",delivery_channel="c")
    with pytest.raises(DomainRuleViolation): svc.deliver_inject(sim,inject)
    svc.start_simulation(sim); assert svc.deliver_inject(sim,inject).delivered_at is not None

def test_evaluation_and_improvement():
    ev=Evaluation(simulation_id=uuid4(),criteria_results={"c":80},capability_scores={"x":60},confidence_level="high")
    assert EvaluationService().calculate_simulation_score(ev)==70
    plan=ImprovementPlan(community_id=uuid4(),source_simulation_id=ev.simulation_id,actions=[ImprovementService().create_improvement_action("a",1,date(2020,1,1))])
    assert len(ImprovementService().identify_overdue_actions(plan))==1
