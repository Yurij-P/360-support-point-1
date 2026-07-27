import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tps360.api import dependencies
from tps360.api.main import app
from tps360.api.routers import sessions as sessions_router
from tps360.db import orm_models  # noqa: F401
from tps360.db.base import Base
from tps360.db.orm_models import (
    AssessmentRow,
    CommunityRow,
    DirectiveRow,
    RefreshTokenRow,
    SessionRow,
    SimulationRow,
)
from tps360.db.session import get_db
from tps360.simulation.services.event_broadcaster import broadcaster

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def setup_test_db(test_engine):
    testing_session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    with test_engine.begin() as connection:
        for model in (
            DirectiveRow,
            SessionRow,
            AssessmentRow,
            SimulationRow,
            CommunityRow,
            RefreshTokenRow,
        ):
            connection.execute(delete(model))

    dependencies.preparedness_profiles.items.clear()
    dependencies.risks_registry.clear()
    dependencies.improvement_plans_registry.clear()
    broadcaster._history.clear()
    broadcaster._listeners.clear()
    sessions_router.lobby_service._rooms.clear()
    sessions_router.aar_telemetry_service._telemetry_log.clear()
    sessions_router.aar_telemetry_service._participant_memory.clear()
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
