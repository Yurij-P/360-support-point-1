from datetime import datetime, timezone
from uuid import UUID

from tps360.core.domain.enums import LifecycleStatus
from tps360.core.domain.models import Decision, Inject, Simulation
from tps360.core.exceptions import DomainRuleViolation


class SimulationService:
    def create_simulation(self, scenario_id: UUID, community_id: UUID) -> Simulation:
        return Simulation(scenario_id=scenario_id, community_id=community_id)

    def start_simulation(self, simulation: Simulation) -> Simulation:
        if simulation.status not in {LifecycleStatus.DRAFT, LifecycleStatus.SCHEDULED}:
            raise DomainRuleViolation("Only draft or scheduled simulations can start")
        simulation.status = LifecycleStatus.ACTIVE
        simulation.started_at = datetime.now(timezone.utc)
        return simulation

    def deliver_inject(self, simulation: Simulation, inject: Inject) -> Inject:
        if simulation.status is not LifecycleStatus.ACTIVE:
            raise DomainRuleViolation("Injects can be delivered only to active simulations")
        inject.delivered_at = datetime.now(timezone.utc)
        simulation.timeline.append({"inject_id": str(inject.id), "event": "delivered"})
        return inject

    def record_decision(self, simulation: Simulation, decision: Decision) -> Simulation:
        if simulation.status is not LifecycleStatus.ACTIVE:
            raise DomainRuleViolation("Decisions can be recorded only during an active simulation")
        simulation.decisions.append(decision)
        return simulation

    def pause_simulation(self, simulation: Simulation) -> Simulation:
        if simulation.status is not LifecycleStatus.ACTIVE:
            raise DomainRuleViolation("Only active simulations can be paused")
        simulation.status = LifecycleStatus.PAUSED
        return simulation

    def complete_simulation(self, simulation: Simulation) -> Simulation:
        if simulation.status not in {LifecycleStatus.ACTIVE, LifecycleStatus.PAUSED}:
            raise DomainRuleViolation("Only active or paused simulations can complete")
        simulation.status = LifecycleStatus.COMPLETED
        simulation.completed_at = datetime.now(timezone.utc)
        return simulation
