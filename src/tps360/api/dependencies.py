from uuid import UUID

from tps360.assessment.repositories import PreparednessProfileRepository
from tps360.core.domain.models import ImprovementPlan, Risk
from tps360.core.repositories import (
    AssessmentRepository,
    CommunityRepository,
    ScenarioRepository,
    SimulationRepository,
)
from tps360.simulation.repositories import SessionRepository

communities = CommunityRepository()
scenarios = ScenarioRepository()
simulations = SimulationRepository()
sessions = SessionRepository()
assessments = AssessmentRepository()
preparedness_profiles = PreparednessProfileRepository()
risks_registry: dict[UUID, list[Risk]] = {}
improvement_plans_registry: dict[UUID, ImprovementPlan] = {}
