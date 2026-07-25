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
