from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

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

router = APIRouter(prefix="/simulations", tags=["simulations"])
service = SimulationService()
community_catalog = CommunityCatalogService()
scenario_service = ScenarioCatalogService()



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
def get_simulation_context_snapshot(session_id: str) -> SimulationContextSnapshotReadModel:
    passport = community_catalog.get_passport("a29d6fbd-02c3-4d43-a651-7efd6fbd02c3")
    scenario = scenario_service.get_scenario("scen_flooding_v1")
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
