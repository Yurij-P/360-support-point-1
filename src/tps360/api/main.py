from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    assessments,
    communities,
    directives,
    events,
    preparedness_profiles,
    risks,
    scenarios,
    sessions,
    simulations,
)

app = FastAPI(title="TPS360 API", version="0.1.0")

LOCAL_PARTICIPANT_ORIGINS = ["http://localhost:3001", "http://127.0.0.1:3001"]
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
):
    app.include_router(router)


