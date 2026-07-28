from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.simulation.domain.task_directive import DirectivePriority, DirectiveStatus

client = TestClient(app)


def test_create_and_get_directive_api() -> None:
    payload = {
        "session_id": "session_api_1",
        "issuer_role_id": "facilitator",
        "assignee_role_id": "head_of_medical",
        "title": "Establish Triage Point",
        "description": "Set up medical triage near central square",
        "target_round": 2,
        "priority": "HIGH",
    }
    create_resp = client.post("/directives", json=payload)
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert data["title"] == "Establish Triage Point"
    assert data["status"] == DirectiveStatus.PROPOSED
    assert data["priority"] == DirectivePriority.HIGH
    assert data["is_terminal"] is False

    directive_id = data["id"]
    get_resp = client.get(f"/directives/{directive_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == directive_id


def test_create_directive_rejects_unauthorized_issuer() -> None:
    # A rank-and-file member may not issue a directive (ADR-0015).
    payload = {
        "session_id": "session_api_authz",
        "issuer_role_id": "vol-fire-member",
        "assignee_role_id": "emerg-dsns",
        "title": "Illegal order",
        "description": "Member trying to task a functional lead",
        "target_round": 2,
    }
    resp = client.post("/directives", json=payload)
    assert resp.status_code == 403


def test_create_directive_allows_lead_to_own_member() -> None:
    payload = {
        "session_id": "session_api_authz_ok",
        "issuer_role_id": "vol-fire-commander",
        "assignee_role_id": "vol-fire-member",
        "title": "Deploy to sector 3",
        "description": "Commander tasks own team member",
        "target_round": 2,
    }
    resp = client.post("/directives", json=payload)
    assert resp.status_code == 200


def test_directive_api_transition_and_reporting() -> None:
    payload = {
        "session_id": "session_api_2",
        "issuer_role_id": "facilitator",
        "assignee_role_id": "logistics_officer",
        "title": "Distribute Water Supply",
        "description": "Deliver 500L bottled water",
        "target_round": 3,
    }
    create_data = client.post("/directives", json=payload).json()
    directive_id = create_data["id"]

    # Assign
    res1 = client.post(
        f"/directives/{directive_id}/transition",
        json={"new_status": "ASSIGNED", "round_number": 1},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "ASSIGNED"

    # In progress
    res2 = client.post(
        f"/directives/{directive_id}/transition",
        json={"new_status": "IN_PROGRESS", "round_number": 2},
    )
    assert res2.json()["status"] == "IN_PROGRESS"

    # Submit report
    res3 = client.post(
        f"/directives/{directive_id}/transition",
        json={
            "new_status": "SUBMITTED",
            "round_number": 3,
            "completion_report": "Water successfully distributed to sectors 1 and 2.",
        },
    )
    assert res3.status_code == 200
    assert res3.json()["status"] == "SUBMITTED"
    assert res3.json()["completion_report"] == "Water successfully distributed to sectors 1 and 2."


def test_list_session_directives_api() -> None:
    session_id = "session_api_list"
    client.post(
        "/directives",
        json={
            "session_id": session_id,
            "issuer_role_id": "facilitator",
            "assignee_role_id": "role_a",
            "title": "Task A",
            "target_round": 1,
        },
    )
    client.post(
        "/directives",
        json={
            "session_id": session_id,
            "issuer_role_id": "facilitator",
            "assignee_role_id": "role_b",
            "title": "Task B",
            "target_round": 1,
        },
    )

    all_resp = client.get(f"/directives/session/{session_id}")
    assert len(all_resp.json()) == 2

    filtered_resp = client.get(f"/directives/session/{session_id}?role_id=role_a")
    assert len(filtered_resp.json()) == 1
    assert filtered_resp.json()[0]["assignee_role_id"] == "role_a"
