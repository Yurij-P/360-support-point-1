from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="TPS360 API", version="0.2.8")

LOCAL_PARTICIPANT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_PARTICIPANT_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Participant-Token"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_model=None)
@app.get("/ui", response_model=None)
def read_root_ui() -> Any:
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": "TPS360 Operational Headquarters API",
        "version": "0.2.8",
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
