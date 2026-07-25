import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import (
    assessments,
    communities,
    preparedness_profiles,
    risks,
    scenarios,
    simulations,
)

app = FastAPI(title="TPS360 API", version="0.1.0")

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
    simulations.router,
    preparedness_profiles.router,
):
    app.include_router(router)


