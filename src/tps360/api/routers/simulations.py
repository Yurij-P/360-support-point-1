from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from tps360.api.dependencies import get_simulation_repo
from tps360.community.services import CommunityCatalogService
from tps360.core.domain.models import Decision, Inject, Simulation
from tps360.core.exceptions import NotFoundError
from tps360.core.services import SimulationService
from tps360.db.repositories import SQLSimulationRepository
from tps360.simulation.domain import (
    SimulationContextSnapshotReadModel,
    SimulationRoundClock,
)
from tps360.simulation.services import ScenarioCatalogService
from tps360.simulation.services.card_supply import initial_hand
from tps360.simulation.services.crisis_demand import estimate_demand, resource_gap
from tps360.simulation.services.participant_engagement import build_coverage_plan
from tps360.simulation.services.resource_estimator import estimate_role_resources

router = APIRouter(prefix="/simulations", tags=["simulations"])
service = SimulationService()
community_catalog = CommunityCatalogService()
scenario_service = ScenarioCatalogService()


class CrisisPlanRequest(BaseModel):
    community_id: str = Field(min_length=1)  # KATOTTG code
    hazard_type: str = Field(min_length=1)
    roster: list[str] = Field(default_factory=list)
    hazard_radius_km: float = Field(default=1.0, gt=0.0)
    severity: float = Field(default=1.0, gt=0.0)
    affected_population: int | None = Field(default=None, ge=0)


class CoverageResponse(BaseModel):
    engaged: list[str]
    idle: list[str]
    secondary_conditions: dict[str, str]
    coverage_pct: float


class CrisisPlanResponse(BaseModel):
    community_id: str
    community_name: str
    hazard_type: str
    coverage: CoverageResponse
    endowment: dict[str, dict[str, Decimal]]
    demand: dict[str, Decimal]
    gap: dict[str, Decimal]
    card_hands: dict[str, list[str]]


@router.post("/crisis-plan", response_model=CrisisPlanResponse)
def build_crisis_plan(req: CrisisPlanRequest) -> CrisisPlanResponse:
    """Tie the resource+crisis algorithm together for a community and roster:
    endowment (estimator) -> demand -> gap, participant coverage and card hands.
    """
    try:
        passport = community_catalog.get_passport(req.community_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    affected = (
        req.affected_population
        if req.affected_population is not None
        else passport.total_population
    )
    roster = list(dict.fromkeys(req.roster))

    plan = build_coverage_plan(req.hazard_type, roster)
    endowment = {role: estimate_role_resources(role, passport) for role in roster}

    pooled: dict[str, Decimal] = {}
    for res_map in endowment.values():
        for key, qty in res_map.items():
            pooled[key] = pooled.get(key, Decimal("0")) + qty

    demand = estimate_demand(req.hazard_type, affected, req.hazard_radius_km, req.severity)
    gap = resource_gap(demand, pooled)
    card_hands = {role: initial_hand(role, req.hazard_type) for role in roster}

    return CrisisPlanResponse(
        community_id=passport.community_id,
        community_name=passport.name,
        hazard_type=req.hazard_type,
        coverage=CoverageResponse(
            engaged=list(plan.engaged),
            idle=list(plan.idle),
            secondary_conditions=plan.secondary_conditions,
            coverage_pct=plan.coverage_pct,
        ),
        endowment=endowment,
        demand=demand,
        gap=gap,
        card_hands=card_hands,
    )



def item(sid: UUID, simulation_repo: SQLSimulationRepository) -> Simulation:
    try:
        return simulation_repo.get(sid)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))


@router.post("")
def create(
    simulation: Simulation, simulation_repo: SQLSimulationRepository = Depends(get_simulation_repo)
) -> Simulation:
    return simulation_repo.add(simulation)


@router.get("/{simulation_id}")
def get_simulation(
    simulation_id: UUID, simulation_repo: SQLSimulationRepository = Depends(get_simulation_repo)
) -> Simulation:
    return item(simulation_id, simulation_repo)


@router.get("/{session_id}/context-snapshot", response_model=SimulationContextSnapshotReadModel)
def get_simulation_context_snapshot(
    session_id: str,
    community_id: str = Query(..., min_length=1),
    scenario_id: str = Query(..., min_length=1),
) -> SimulationContextSnapshotReadModel:
    try:
        passport = community_catalog.get_passport(community_id)
        scenario = scenario_service.get_scenario(scenario_id)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc))
    return SimulationContextSnapshotReadModel(
        session_id=session_id,
        community_passport=passport,
        scenario_id=scenario.id,
        scenario_title=scenario.title,
        threat_categories=(scenario.threat_category,),
        time_dilation_clock=SimulationRoundClock(
            real_round_minutes=scenario.target_round_duration,
            velocity=scenario.crisis_velocity,
        ),
        is_osm_bounded=True,
        bounding_box=passport.bounding_box,
    )




@router.post("/{simulation_id}/start")
def start(
    simulation_id: UUID, simulation_repo: SQLSimulationRepository = Depends(get_simulation_repo)
) -> Simulation:
    simulation = service.start_simulation(item(simulation_id, simulation_repo))
    return simulation_repo.save(simulation)


@router.post("/{simulation_id}/injects/{inject_id}/deliver")
def deliver(
    simulation_id: UUID,
    inject_id: UUID,
    inject: Inject,
    simulation_repo: SQLSimulationRepository = Depends(get_simulation_repo),
) -> Inject:
    if inject.id != inject_id:
        raise HTTPException(400, "Inject id mismatch")
    simulation = item(simulation_id, simulation_repo)
    delivered = service.deliver_inject(simulation, inject)
    simulation_repo.save(simulation)
    return delivered


@router.post("/{simulation_id}/decisions")
def decision(
    simulation_id: UUID,
    decision: Decision,
    simulation_repo: SQLSimulationRepository = Depends(get_simulation_repo),
) -> Simulation:
    simulation = service.record_decision(item(simulation_id, simulation_repo), decision)
    return simulation_repo.save(simulation)


@router.post("/{simulation_id}/complete")
def complete(
    simulation_id: UUID, simulation_repo: SQLSimulationRepository = Depends(get_simulation_repo)
) -> Simulation:
    simulation = service.complete_simulation(item(simulation_id, simulation_repo))
    return simulation_repo.save(simulation)
