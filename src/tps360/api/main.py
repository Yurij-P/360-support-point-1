from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from tps360.community.services.catalog_service import CommunityCatalogItem, CommunityCatalogService
from tps360.db import orm_models  # noqa: F401
from tps360.db.base import Base
from tps360.db.engine import engine

from .routers import (
    assessments,
    communities,
    directives,
    events,
    preparedness_profiles,
    risks,
    roles,
    scenarios,
    sessions,
    simulations,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="TPS360 API", version="0.1.0", lifespan=lifespan)

LOCAL_PARTICIPANT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_PARTICIPANT_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Participant-Token"],
)

@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "name": "TPS360 Operational Headquarters API",
        "version": "0.2.1",
        "status": "running",
        "docs": "/docs",
    }



@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api_v1_router = APIRouter(prefix="/api/v1")
frontend_catalog_service = CommunityCatalogService()


@api_v1_router.get("/communities/catalog", response_model=list[CommunityCatalogItem])
def get_frontend_communities_catalog(
    query: str | None = Query(default=None),
    region: str | None = Query(default=None),
    min_preparedness: float | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[CommunityCatalogItem]:
    return frontend_catalog_service.search_catalog(
        query=query,
        region=region,
        min_preparedness=min_preparedness,
        limit=limit,
        offset=offset,
    )


app.include_router(api_v1_router)
app.include_router(sessions.router, prefix="/api/v1")


for router in (
    communities.router,
    risks.router,
    assessments.router,
    scenarios.router,
    sessions.router,
    simulations.router,
    preparedness_profiles.router,
    directives.router,
    events.router,
    roles.router,
):
    app.include_router(router)
