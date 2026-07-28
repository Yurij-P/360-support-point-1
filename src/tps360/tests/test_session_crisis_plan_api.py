from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def _katottg_code() -> str:
    return client.get("/communities/catalog").json()["items"][0]["community_id"]


def test_session_crisis_plan_end_to_end() -> None:
    code = _katottg_code()

    created = client.post(
        "/sessions",
        json={"community_id": code, "facilitator_name": "F", "player_capacity": 5},
    )
    assert created.status_code == 200
    session_id = created.json()["id"]
    ftoken = created.json()["facilitator_token"]

    crisis = client.post(
        f"/sessions/{session_id}/crisis/define",
        headers={"X-Facilitator-Token": ftoken},
        json={
            "title": "Пожежа",
            "category": "natural",
            "primary_hazard": "wildfire",
            "description": "Лісова пожежа поблизу села",
        },
    )
    assert crisis.status_code == 200

    joined = client.post(f"/sessions/{session_id}/lobby/join", json={"display_name": "Гравець"})
    assert joined.status_code == 200
    participant_id = joined.json()["participant_id"]

    assigned = client.post(
        f"/sessions/{session_id}/lobby/assign-role",
        json={"participant_id": participant_id, "role_id": "emerg-dsns"},
    )
    assert assigned.status_code == 200

    plan = client.get(f"/sessions/{session_id}/crisis-plan")
    assert plan.status_code == 200
    data = plan.json()
    assert data["hazard_type"] == "wildfire"
    assert "emerg-dsns" in data["coverage"]["engaged"]
    assert "emerg-dsns" in data["endowment"]
    assert data["demand"]  # non-empty for a fire


def test_session_crisis_plan_requires_defined_crisis() -> None:
    code = _katottg_code()
    created = client.post(
        "/sessions",
        json={"community_id": code, "facilitator_name": "F", "player_capacity": 5},
    )
    session_id = created.json()["id"]
    resp = client.get(f"/sessions/{session_id}/crisis-plan")
    assert resp.status_code == 409  # crisis not defined
