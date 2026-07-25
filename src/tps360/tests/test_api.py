from uuid import uuid4

from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_community():
    response = client.post(
        "/communities",
        json={
            "name": "Громада",
            "code": "API-1",
            "oblast": "Київська",
            "population": 1,
            "area_km2": 1,
        },
    )
    assert response.status_code == 200 and response.json()["code"] == "API-1"


def test_facilitated_session_startup_flow():
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Фасилітатор",
            "player_capacity": 2,
        },
    )
    assert created.status_code == 200
    session_id = created.json()["id"]

    joined = client.post(
        f"/sessions/{session_id}/participants",
        json={"display_name": "Гравець 1"},
    )
    assert joined.status_code == 200
    participant_id = joined.json()["id"]

    blocked = client.post(f"/sessions/{session_id}/start")
    assert blocked.status_code == 409

    assigned = client.put(
        f"/sessions/{session_id}/participants/{participant_id}/role",
        json={"role_id": str(uuid4())},
    )
    assert assigned.status_code == 200

    started = client.post(f"/sessions/{session_id}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "active"
