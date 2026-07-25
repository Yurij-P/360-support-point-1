from uuid import UUID

from tps360.assessment.repositories import PreparednessProfileRepository

from tps360.core.domain.models import ImprovementPlan, Risk
from tps360.core.repositories import (
    AssessmentRepository,
    CommunityRepository,
    ScenarioRepository,
    SimulationRepository,
)

communities = CommunityRepository()
scenarios = ScenarioRepository()
simulations = SimulationRepository()
assessments = AssessmentRepository()
preparedness_profiles = PreparednessProfileRepository()
risks_registry: dict[UUID, list[Risk]] = {}
improvement_plans_registry: dict[UUID, ImprovementPlan] = {}


