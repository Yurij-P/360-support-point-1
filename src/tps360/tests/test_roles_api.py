from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.simulation.services.role_catalog_service import RoleCatalogService

client = TestClient(app)


# ── catalog service unit tests ────────────────────────────────────────────────

def test_catalog_contains_23_entries() -> None:
    assert len(RoleCatalogService().list_entries()) == 23


def test_catalog_contains_7_categories() -> None:
    entries = RoleCatalogService().list_entries()
    assert len({e.category_key for e in entries}) == 7


def test_catalog_filter_by_category_key_local_government() -> None:
    entries = RoleCatalogService().list_entries(category_key="local_government")
    assert len(entries) == 4
    assert all(e.category_key == "local_government" for e in entries)


def test_catalog_filter_by_unknown_category_returns_empty() -> None:
    assert RoleCatalogService().list_entries(category_key="unknown") == ()


def test_catalog_get_entry_by_known_role_id() -> None:
    entry = RoleCatalogService().get_entry("emerg-dsns")
    assert entry is not None
    assert entry.position == "Представник ДСНС"
    assert entry.category_key == "emergency_services"


def test_catalog_get_entry_unknown_returns_none() -> None:
    assert RoleCatalogService().get_entry("no-such-role") is None


def test_all_role_ids_are_unique() -> None:
    ids = [e.role_id for e in RoleCatalogService().list_entries()]
    assert len(ids) == len(set(ids))


def test_all_positions_are_non_empty() -> None:
    for entry in RoleCatalogService().list_entries():
        assert entry.position.strip()
        assert entry.category.strip()
        assert entry.category_key.strip()


# ── GET /roles/catalog ────────────────────────────────────────────────────────

def test_get_roles_catalog_returns_23_items() -> None:
    resp = client.get("/roles/catalog")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 23
    assert body["categories"] == 7
    assert len(body["items"]) == 23


def test_get_roles_catalog_filter_by_category_key() -> None:
    resp = client.get("/roles/catalog?category_key=starosty")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert all(item["category_key"] == "starosty" for item in body["items"])


def test_get_roles_catalog_unknown_category_returns_empty() -> None:
    resp = client.get("/roles/catalog?category_key=nonexistent")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ── GET /roles/catalog/{role_id} ─────────────────────────────────────────────

def test_get_role_catalog_entry_known() -> None:
    resp = client.get("/roles/catalog/local-gov-head")
    assert resp.status_code == 200
    body = resp.json()
    assert body["role_id"] == "local-gov-head"
    assert body["position"] == "Голова громади"
    assert body["category_key"] == "local_government"


def test_get_role_catalog_entry_not_found() -> None:
    resp = client.get("/roles/catalog/no-such-role")
    assert resp.status_code == 404


# ── GET /sessions/{id}/roles/me ───────────────────────────────────────────────

@pytest.fixture()
def session_with_participant_and_role() -> dict[str, str]:
    """Creates a session, joins a participant, assigns a role; returns tokens."""
    from uuid import uuid4
    role_id = uuid4()
    create_resp = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Facilitator",
            "player_capacity": 5,
            "role_profiles": [
                {
                    "role_id": str(role_id),
                    "title": "Голова громади",
                    "category": "Органи місцевого самоврядування",
                    "briefing": "Бриф для голови громади",
                    "allowed_actions": ["approve", "delegate"],
                    "visibility_rules": ["full"],
                }
            ],
        },
    )
    assert create_resp.status_code == 200
    body = create_resp.json()
    session_id = body["id"]
    facilitator_token = body["facilitator_token"]
    join_token = body["join_token"]

    join_resp = client.post(
        f"/sessions/{session_id}/participants/join",
        json={"display_name": "Olena", "join_token": join_token},
    )
    assert join_resp.status_code == 200
    join_body = join_resp.json()
    participant_token = join_body["participant_token"]
    participant_id = str(join_body["participant_id"])

    assign_resp = client.put(
        f"/sessions/{session_id}/participants/{participant_id}/role",
        json={"role_id": str(role_id)},
        headers={"X-Facilitator-Token": facilitator_token},
    )
    assert assign_resp.status_code == 200

    return {"session_id": session_id, "participant_token": participant_token, "role_id": str(role_id)}


def test_get_my_role_no_token_returns_401() -> None:
    resp = client.get(f"/sessions/{uuid4()}/roles/me")
    assert resp.status_code == 401


def test_get_my_role_invalid_token_returns_401(session_with_participant_and_role: dict[str, str]) -> None:
    session_id = session_with_participant_and_role["session_id"]
    resp = client.get(f"/sessions/{session_id}/roles/me", headers={"X-Participant-Token": "bad-token"})
    assert resp.status_code == 401


def test_get_my_role_session_not_found_returns_404() -> None:
    resp = client.get(f"/sessions/{uuid4()}/roles/me", headers={"X-Participant-Token": "any"})
    assert resp.status_code == 404


def test_get_my_role_returns_assigned_profile(session_with_participant_and_role: dict[str, str]) -> None:
    data = session_with_participant_and_role
    resp = client.get(
        f"/sessions/{data['session_id']}/roles/me",
        headers={"X-Participant-Token": data["participant_token"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["role_id"] == data["role_id"]
    assert body["title"] == "Голова громади"
    assert body["lifecycle"] == "role_assigned"
    assert "approve" in body["allowed_actions"]
