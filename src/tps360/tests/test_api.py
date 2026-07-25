from uuid import uuid4

from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def role_profile(role_id: str) -> dict[str, object]:
    return {
        "role_id": role_id,
        "title": "Test role",
        "category": "Test category",
        "briefing": "Test briefing",
    }



def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_community():
    response = client.post(
        "/communities",
        json={
            "name": "Р В РІР‚СљР РЋР вЂљР В РЎвЂўР В РЎВР В Р’В°Р В РўвЂР В Р’В°",
            "code": "API-1",
            "oblast": "Р В РЎв„ўР В РЎвЂР РЋРІР‚вЂќР В Р вЂ Р РЋР С“Р РЋР Р‰Р В РЎвЂќР В Р’В°",
            "population": 1,
            "area_km2": 1,
        },
    )
    assert response.status_code == 200 and response.json()["code"] == "API-1"


def test_facilitated_session_startup_flow():
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Р В Р’В¤Р В Р’В°Р РЋР С“Р В РЎвЂР В Р’В»Р РЋРІР‚вЂњР РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р В РЎвЂўР РЋР вЂљ",
            "player_capacity": 2,
            "role_profiles": [role_profile(role_id)],
        },
    )
    assert created.status_code == 200
    session_id = created.json()["id"]
    facilitator_headers = {
        "X-Facilitator-Token": created.json()["facilitator_token"]
    }

    joined = client.post(
        f"/sessions/{session_id}/participants",
        json={"display_name": "Р В РІР‚СљР РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’ВµР РЋРІР‚В Р РЋР Р‰ 1"},
    )
    assert joined.status_code == 200
    participant_id = joined.json()["id"]

    blocked = client.post(
        f"/sessions/{session_id}/start", headers=facilitator_headers
    )
    assert blocked.status_code == 409

    assigned = client.put(
        f"/sessions/{session_id}/participants/{participant_id}/role",
        json={"role_id": role_id},
        headers=facilitator_headers,
    )
    assert assigned.status_code == 200

    started = client.post(
        f"/sessions/{session_id}/start", headers=facilitator_headers
    )
    assert started.status_code == 200
    assert started.json()["status"] == "active"


def test_assigning_role_to_unknown_participant_returns_not_found():
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Р В Р’В¤Р В Р’В°Р РЋР С“Р В РЎвЂР В Р’В»Р РЋРІР‚вЂњР РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р В РЎвЂўР РЋР вЂљ",
            "player_capacity": 1,
            "role_profiles": [role_profile(role_id)],
        },
    )
    session_id = created.json()["id"]
    facilitator_headers = {
        "X-Facilitator-Token": created.json()["facilitator_token"]
    }

    response = client.put(
        f"/sessions/{session_id}/participants/{uuid4()}/role",
        json={"role_id": role_id},
        headers=facilitator_headers,
    )

    assert response.status_code == 404


def test_session_cannot_be_started_twice():
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Р В Р’В¤Р В Р’В°Р РЋР С“Р В РЎвЂР В Р’В»Р РЋРІР‚вЂњР РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р В РЎвЂўР РЋР вЂљ",
            "player_capacity": 1,
            "role_profiles": [role_profile(role_id)],
        },
    )
    session_id = created.json()["id"]
    facilitator_headers = {
        "X-Facilitator-Token": created.json()["facilitator_token"]
    }
    joined = client.post(
        f"/sessions/{session_id}/participants",
        json={"display_name": "Р В РІР‚СљР РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’ВµР РЋРІР‚В Р РЋР Р‰ 1"},
    )
    client.put(
        f"/sessions/{session_id}/participants/{joined.json()['id']}/role",
        json={"role_id": role_id},
        headers=facilitator_headers,
    )
    assert (
        client.post(f"/sessions/{session_id}/start", headers=facilitator_headers).status_code
        == 200
    )

    repeated = client.post(
        f"/sessions/{session_id}/start", headers=facilitator_headers
    )

    assert repeated.status_code == 409


def test_facilitator_actions_require_the_generated_token():
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Р В Р’В¤Р В Р’В°Р РЋР С“Р В РЎвЂР В Р’В»Р РЋРІР‚вЂњР РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р В РЎвЂўР РЋР вЂљ",
            "player_capacity": 1,
            "role_profiles": [role_profile(role_id)],
        },
    )
    session_id = created.json()["id"]
    token = created.json()["facilitator_token"]
    joined = client.post(
        f"/sessions/{session_id}/participants",
        json={"display_name": "Р В РІР‚СљР РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’ВµР РЋРІР‚В Р РЋР Р‰ 1"},
    )
    role_url = f"/sessions/{session_id}/participants/{joined.json()['id']}/role"

    missing = client.put(role_url, json={"role_id": str(uuid4())})
    invalid = client.put(
        role_url,
        json={"role_id": str(uuid4())},
        headers={"X-Facilitator-Token": "not-the-token"},
    )
    authorized = client.put(
        role_url,
        json={"role_id": role_id},
        headers={"X-Facilitator-Token": token},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 403
    assert authorized.status_code == 200


def test_facilitator_token_is_returned_once_and_not_exposed_by_session_reads():
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Р В Р’В¤Р В Р’В°Р РЋР С“Р В РЎвЂР В Р’В»Р РЋРІР‚вЂњР РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р В РЎвЂўР РЋР вЂљ",
            "player_capacity": 1,
            "role_profiles": [role_profile(role_id)],
        },
    )

    session_id = created.json()["id"]
    fetched = client.get(
        f"/sessions/{session_id}",
        headers={"X-Facilitator-Token": created.json()["facilitator_token"]},
    )

    assert created.json()["facilitator_token"]
    assert "facilitator_token" not in fetched.json()
    assert "facilitator_token_digest" not in fetched.json()


def test_session_openapi_schemas_do_not_expose_facilitator_token_digest():
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    assert "facilitator_token_digest" not in schemas["SessionResponse"]["properties"]
    assert "facilitator_token_digest" not in schemas["CreateSessionResponse"]["properties"]
    assert "facilitator_token_digest" not in schemas["SessionResponse"].get("required", [])
    assert "facilitator_token_digest" not in schemas["CreateSessionResponse"].get(
        "required", []
    )
