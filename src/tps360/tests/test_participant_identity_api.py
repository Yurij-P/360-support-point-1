from uuid import uuid4

from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def create_session() -> tuple[str, str, str, str]:
    role_id = str(uuid4())
    response = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Facilitator",
            "player_capacity": 2,
            "role_profiles": [
                {
                    "role_id": role_id,
                    "title": "Community coordinator",
                    "category": "Community leadership",
                    "briefing": "Coordinate local response decisions.",
                    "allowed_actions": ["coordinate"],
                    "visibility_rules": ["own_role_data"],
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    return body["id"], body["facilitator_token"], body["join_token"], role_id


def test_join_token_is_separate_from_facilitator_token_and_reconnect_is_idempotent() -> None:
    session_id, facilitator_token, join_token, _ = create_session()
    joined = client.post(
        f"/sessions/{session_id}/participants/join",
        json={"join_token": join_token, "display_name": "Participant One"},
    )
    assert joined.status_code == 200
    first = joined.json()
    assert first["participant_token"]
    assert first["role_assigned"] is False
    assert first["role_profile"] is None
    assert first["lifecycle"] == "role_pending"

    facilitator_as_participant = client.get(
        f"/sessions/{session_id}/participant",
        headers={"X-Participant-Token": facilitator_token},
    )
    assert facilitator_as_participant.status_code == 403

    reconnected = client.post(
        f"/sessions/{session_id}/participants/join",
        json={
            "participant_token": first["participant_token"],
            "display_name": "Changed Name Must Not Replace Identity",
        },
    )
    assert reconnected.status_code == 200
    assert reconnected.json()["participant_id"] == first["participant_id"]
    assert reconnected.json()["participant_token"] is None
    assert reconnected.json()["reconnect_status"] == "restored"

    profile = client.get(
        f"/sessions/{session_id}/participant",
        headers={"X-Participant-Token": first["participant_token"]},
    )
    assert profile.status_code == 200
    assert profile.json()["participant_id"] == first["participant_id"]
    assert profile.json()["display_name"] == "Participant One"
    assert profile.json()["reconnect_status"] == "restored"
    assert "facilitator_token" not in profile.json()
    assert "participants" not in profile.json()
    assert "decisions" not in profile.json()


def test_participant_endpoint_requires_valid_participant_token() -> None:
    session_id, _, join_token, _ = create_session()
    joined = client.post(
        f"/sessions/{session_id}/participants/join",
        json={"join_token": join_token, "display_name": "Participant One"},
    )
    assert joined.status_code == 200
    assert client.get(f"/sessions/{session_id}/participant").status_code == 401
    assert client.get(
        f"/sessions/{session_id}/participant",
        headers={"X-Participant-Token": "invalid"},
    ).status_code == 403


def test_only_facilitator_can_assign_role_and_participant_receives_profile() -> None:
    session_id, facilitator_token, join_token, role_id = create_session()
    joined = client.post(
        f"/sessions/{session_id}/participants/join",
        json={"join_token": join_token, "display_name": "Participant One"},
    )
    participant = joined.json()
    role_url = f"/sessions/{session_id}/participants/{participant['participant_id']}/role"

    assert client.put(role_url, json={"role_id": role_id}).status_code == 401
    assigned = client.put(
        role_url,
        json={"role_id": role_id},
        headers={"X-Facilitator-Token": facilitator_token},
    )
    assert assigned.status_code == 200

    visible = client.get(
        f"/sessions/{session_id}/participant",
        headers={"X-Participant-Token": participant["participant_token"]},
    )
    assert visible.status_code == 200
    body = visible.json()
    assert body["role_assigned"] is True
    assert body["role_id"] == role_id
    assert body["role_profile"]["role_id"] == role_id
    assert body["lifecycle"] == "role_assigned"

    invalid_role = client.put(
        role_url,
        json={"role_id": str(uuid4())},
        headers={"X-Facilitator-Token": facilitator_token},
    )
    assert invalid_role.status_code == 409