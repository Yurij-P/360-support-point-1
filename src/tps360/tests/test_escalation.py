from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.simulation.services.command_hierarchy import can_escalate

client = TestClient(app)


def test_can_escalate_rules() -> None:
    # member -> own-category lead: allowed
    assert can_escalate("vol-fire-member", "vol-fire-commander")
    # member -> foreign lead: refused
    assert not can_escalate("vol-fire-member", "edu-director")
    # member -> command tier (skip-level to HQ): allowed
    assert can_escalate("vol-fire-member", "local-gov-head")
    # anyone -> facilitator: allowed
    assert can_escalate("vol-fire-member", "facilitator")
    # sideways / downward refused
    assert not can_escalate("emerg-dsns", "emerg-police")
    assert not can_escalate("local-gov-head", "emerg-dsns")


def test_raise_and_list_escalation_api() -> None:
    sess = "sess_escalation_1"
    resp = client.post(
        f"/sessions/{sess}/escalations",
        json={
            "requester_role_id": "vol-fire-member",
            "target_role_id": "vol-fire-commander",
            "subject": "Потрібне підкріплення",
            "detail": "Вогонь поширюється на сектор 4",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPEN"
    esc_id = data["escalation_id"]

    listed = client.get(f"/sessions/{sess}/escalations", params={"role_id": "vol-fire-commander"})
    assert listed.status_code == 200
    assert any(e["escalation_id"] == esc_id for e in listed.json())

    upd = client.post(
        f"/sessions/{sess}/escalations/{esc_id}/status", json={"status": "acknowledged"}
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "ACKNOWLEDGED"


def test_escalation_api_rejects_downward_request() -> None:
    resp = client.post(
        "/sessions/sess_escalation_2/escalations",
        json={
            "requester_role_id": "local-gov-head",
            "target_role_id": "vol-fire-member",
            "subject": "Downward attempt",
        },
    )
    assert resp.status_code == 403
