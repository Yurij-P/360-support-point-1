from fastapi import Depends
from sqlalchemy.orm import Session

from tps360.assessment.repositories import PreparednessProfileRepository
from tps360.core.domain.community_id import CommunityId
from tps360.core.domain.models import ImprovementPlan, Risk
from tps360.db.repositories import (
    SQLAssessmentRepository,
    SQLCommunityRepository,
    SQLDirectiveRepository,
    SQLSessionRepository,
    SQLSimulationRepository,
)
from tps360.db.session import get_db


def get_community_repo(db: Session = Depends(get_db)) -> SQLCommunityRepository:
    return SQLCommunityRepository(db)


def get_simulation_repo(db: Session = Depends(get_db)) -> SQLSimulationRepository:
    return SQLSimulationRepository(db)


def get_assessment_repo(db: Session = Depends(get_db)) -> SQLAssessmentRepository:
    return SQLAssessmentRepository(db)


def get_session_repo(db: Session = Depends(get_db)) -> SQLSessionRepository:
    return SQLSessionRepository(db)


def get_directive_repo(db: Session = Depends(get_db)) -> SQLDirectiveRepository:
    return SQLDirectiveRepository(db)


preparedness_profiles = PreparednessProfileRepository()
risks_registry: dict[CommunityId, list[Risk]] = {}
improvement_plans_registry: dict[CommunityId, ImprovementPlan] = {}
