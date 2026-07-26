import pytest
from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.services.session_lobby_service import (
    SessionLobbyService,
)

client = TestClient(app)
SESS = "sess_lobby_test_100"


def test_session_lobby_lifecycle() -> None:
    service = SessionLobbyService()
    room = service.create_room(session_id=SESS, capacity=3)
    assert room.session_id == SESS
    assert room.capacity == 3
    assert room.connected_count == 0
    assert room.can_start is False

    # Participant 1 joins
    p1 = service.join_standby_room(session_id=SESS, display_name="Іванко Голова ДСНС")
    assert p1.display_name == "Іванко Голова ДСНС"
    assert p1.is_assigned is False
    assert len(p1.token) > 0

    status = service.get_lobby_status(SESS)
    assert status.connected_count == 1
    assert status.assigned_count == 0
    assert status.can_start is False  # Guard blocks start because P1 has no role!
    assert "без ролі" in status.readiness_message

    # Assign role to P1
    updated_p1 = service.assign_participant_role(
        session_id=SESS, participant_id=p1.participant_id, role_id="head_of_emergency"
    )
    assert updated_p1.is_assigned is True
    assert updated_p1.role_id == "head_of_emergency"

    status_ready = service.get_lobby_status(SESS)
    assert status_ready.assigned_count == 1
    assert status_ready.can_start is True  # Guard passes!


def test_session_lobby_duplicate_role_assignment_fails() -> None:
    service = SessionLobbyService()
    service.create_room(session_id="sess_dup_1", capacity=5)
    p1 = service.join_standby_room("sess_dup_1", "Гравець 1")
    p2 = service.join_standby_room("sess_dup_1", "Гравець 2")

    service.assign_participant_role("sess_dup_1", p1.participant_id, "head_of_emergency")

    with pytest.raises(DomainRuleViolation, match="already assigned"):
        service.assign_participant_role("sess_dup_1", p2.participant_id, "head_of_emergency")


def test_session_lobby_capacity_exceeded_fails() -> None:
    service = SessionLobbyService()
    service.create_room(session_id="sess_cap_1", capacity=1)
    service.join_standby_room("sess_cap_1", "Гравець 1")

    with pytest.raises(DomainRuleViolation, match="reached maximum capacity"):
        service.join_standby_room("sess_cap_1", "Гравець 2")


def test_session_lobby_api_endpoints() -> None:
    sess_id = "sess_api_lobby_999"

    # Join lobby
    response = client.post(f"/sessions/{sess_id}/lobby/join", json={"display_name": "Марія Лікар"})
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Марія Лікар"
    p_id = data["participant_id"]

    # Check status (should be can_start = False)
    status_resp = client.get(f"/sessions/{sess_id}/lobby-status")
    assert status_resp.status_code == 200
    s_data = status_resp.json()
    assert s_data["connected_count"] == 1
    assert s_data["can_start"] is False

    # Assign role
    assign_resp = client.post(
        f"/sessions/{sess_id}/lobby/assign-role",
        json={"participant_id": p_id, "role_id": "chief_medical_officer"},
    )
    assert assign_resp.status_code == 200
    a_data = assign_resp.json()
    assert a_data["role_id"] == "chief_medical_officer"

    # Check status (should be can_start = True)
    status_resp2 = client.get(f"/sessions/{sess_id}/lobby-status")
    assert status_resp2.status_code == 200
    s_data2 = status_resp2.json()
    assert s_data2["can_start"] is True
