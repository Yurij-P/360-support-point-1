from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def _a_community_id() -> str:
    return client.get("/communities/catalog").json()["items"][0]["community_id"]


def test_crisis_plan_ties_everything_together() -> None:
    community_id = _a_community_id()
    payload = {
        "community_id": community_id,
        "hazard_type": "wildfire",
        "roster": ["emerg-dsns", "communal-utility", "edu-director"],
        "hazard_radius_km": 2.0,
        "severity": 0.8,
    }
    resp = client.post("/simulations/crisis-plan", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["community_id"] == community_id
    # coverage: idle school director is pulled in via a secondary condition
    assert data["coverage"]["coverage_pct"] == 100.0
    assert "edu-director" in data["coverage"]["idle"]
    assert "edu-director" in data["coverage"]["secondary_conditions"]
    # endowment per roster role, demand and card hands present
    assert set(data["endowment"]) == {"emerg-dsns", "communal-utility", "edu-director"}
    assert data["demand"]  # non-empty for a fire
    assert data["card_hands"]["emerg-dsns"]


def test_crisis_plan_unknown_community_404() -> None:
    resp = client.post(
        "/simulations/crisis-plan",
        json={"community_id": "ua00000000000000000", "hazard_type": "wildfire", "roster": []},
    )
    assert resp.status_code == 404
