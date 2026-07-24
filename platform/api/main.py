from fastapi import FastAPI
from .routers import assessments, communities, risks, scenarios, simulations

app = FastAPI(title="TPS360 API", version="0.1.0")
@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok"}
for router in (communities.router, risks.router, assessments.router, scenarios.router, simulations.router): app.include_router(router)
