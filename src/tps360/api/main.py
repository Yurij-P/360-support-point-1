import os

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

app = FastAPI(title="TPS360 API", version="0.1.0")

LOCAL_PARTICIPANT_ORIGINS = ["http://localhost:3001", "http://127.0.0.1:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_PARTICIPANT_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Participant-Token"],
)

# Serve static files from the web directory
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
app.mount("/static", StaticFiles(directory=web_dir), name="static")


@app.get("/")
def read_root() -> FileResponse:
    return FileResponse(os.path.join(web_dir, "index.html"))


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


