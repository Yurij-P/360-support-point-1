from uuid import UUID
from fastapi import APIRouter, HTTPException
from tps360.api.dependencies import simulations
from tps360.core.domain.models import Decision, Inject, Simulation
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.core.services import SimulationService
router=APIRouter(prefix="/simulations", tags=["simulations"]); service=SimulationService()
def item(sid: UUID) -> Simulation:
    try: return simulations.get(sid)
    except NotFoundError as exc: raise HTTPException(404, str(exc))
@router.post("")
def create(simulation: Simulation) -> Simulation: return simulations.add(simulation)
@router.post("/{simulation_id}/start")
def start(simulation_id: UUID) -> Simulation: return service.start_simulation(item(simulation_id))
@router.post("/{simulation_id}/injects/{inject_id}/deliver")
def deliver(simulation_id: UUID, inject_id: UUID, inject: Inject) -> Inject:
    if inject.id != inject_id: raise HTTPException(400,"Inject id mismatch")
    return service.deliver_inject(item(simulation_id), inject)
@router.post("/{simulation_id}/decisions")
def decision(simulation_id: UUID, decision: Decision) -> Simulation: return service.record_decision(item(simulation_id), decision)
@router.post("/{simulation_id}/complete")
def complete(simulation_id: UUID) -> Simulation: return service.complete_simulation(item(simulation_id))
