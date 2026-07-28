from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.community.services import CommunityCatalogService
from tps360.simulation.services.resource_estimator import estimate_role_resources

client = TestClient(app)


def test_create_session_with_katottg_binds_estimated_resources() -> None:
    code = client.get("/communities/catalog").json()["items"][0]["community_id"]

    resp = client.post(
        "/sessions",
        json={
            "community_id": code,
            "facilitator_name": "Фасилітатор",
            "player_capacity": 5,
        },
    )
    assert resp.status_code == 200
    session_id = resp.json()["id"]

    ws = client.get(f"/sessions/{session_id}/role-workspace?role_id=communal-utility")
    assert ws.status_code == 200
    available = ws.json()["available_resources"]

    passport = CommunityCatalogService().get_passport(code)
    expected = estimate_role_resources("communal-utility", passport)
    assert Decimal(available["tractors"]) == expected["tractors"]


def test_create_session_unknown_katottg_404() -> None:
    resp = client.post(
        "/sessions",
        json={
            "community_id": "ua00000000000000000",
            "facilitator_name": "F",
            "player_capacity": 5,
        },
    )
    assert resp.status_code == 404


def test_create_session_non_katottg_community_id_skips_binding() -> None:
    # A non-KATOTTG community_id (e.g. legacy UUID string) must not 404; it just
    # falls back to static seeds (no passport bound).
    resp = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "F",
            "player_capacity": 5,
        },
    )
    assert resp.status_code == 200
