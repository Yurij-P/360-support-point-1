from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def legacy_payload() -> dict[str, object]:
    return {
        "schema_version": "participant-decision-draft-0.1",
        "kind": "structured_decision_placeholder",
        "blocks": [],
        "notes": {
            "title": "Temporary response",
            "description": "Legacy prototype payload remains opaque.",
            "rationale": "Backward compatibility.",
        },
    }


def lego_payload() -> dict[str, object]:
    return {
        "schema_version": "participant-decision-lego-1.0",
        "kind": "lego_decision",
        "blocks": [
            {
                "block_id": "task-1",
                "block_type": "action",
                "label": "Set field assessment task",
                "data": {
                    "task_objective": "Assess the water intake site",
                    "task_status": "completed",
                    "report_to_role_ref": "hq-lead",
                },
            },
            {
                "block_id": "responsible-1",
                "block_type": "responsible",
                "label": "Responsible role",
                "data": {"role_ref": "starosta", "executor_type": "participant_role"},
            },
            {
                "block_id": "geo-1",
                "block_type": "geo_area",
                "label": "Observed location",
                "data": {
                    "kind": "point",
                    "lat": 47.12345,
                    "lon": 32.12345,
                    "confidence": "partly_confirmed",
                },
            },
            {
                "block_id": "resource-1",
                "block_type": "resource",
                "label": "Resource need",
                "data": {"resource_type": "generator", "quantity": 1, "priority": "high"},
            },
            {
                "block_id": "condition-1",
                "block_type": "condition",
                "label": "Operational condition",
                "data": {"if": "generator_available", "then": "restart_pump"},
            },
            {
                "block_id": "message-1",
                "block_type": "public_message",
                "label": "Public message",
                "data": {"audience": "residents", "channel": "telegram", "status": "draft"},
            },
            {
                "block_id": "assistance-1",
                "block_type": "assistance_request",
                "label": "Assistance request",
                "data": {"target": "regional_authority", "request": "backup generator"},
            },
            {
                "block_id": "priority-1",
                "block_type": "priority",
                "label": "Priority",
                "data": {"level": "high"},
            },
            {
                "block_id": "timing-1",
                "block_type": "timing",
                "label": "Timing",
                "data": {"kind": "deadline", "value": "PT30M"},
            },
            {
                "block_id": "object-1",
                "block_type": "object",
                "label": "Action object",
                "data": {"object_type": "critical_infrastructure", "name": "water intake"},
            },
            {
                "block_id": "rationale-1",
                "block_type": "rationale",
                "label": "Rationale",
                "data": {"text": "Protect residents and restore minimum water service."},
            },
            {
                "block_id": "result-1",
                "block_type": "expected_result",
                "label": "Expected result",
                "data": {"text": "Verified status reported to headquarters."},
            },
        ],
        "links": [
            {
                "link_id": "link-1",
                "from_block_id": "task-1",
                "to_block_id": "geo-1",
                "relation": "then",
            },
            {
                "link_id": "link-2",
                "from_block_id": "geo-1",
                "to_block_id": "resource-1",
                "relation": "supports",
            },
            {
                "link_id": "link-3",
                "from_block_id": "resource-1",
                "to_block_id": "timing-1",
                "relation": "depends_on",
            },
        ],
        "metadata": {
            "knowledge_scope": "participant_report",
            "shared_operational_picture_candidate": True,
            "created_by": "participant_workspace",
        },
    }


def start_session() -> tuple[str, dict[str, str], dict[str, str], str]:
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Facilitator",
            "player_capacity": 1,
            "role_profiles": [
                {
                    "role_id": role_id,
                    "title": "Starosta",
                    "category": "Community leadership",
                    "briefing": "Assess local conditions.",
                }
            ],
        },
    )
    assert created.status_code == 200
    body = created.json()
    session_id = body["id"]
    facilitator_headers = {"X-Facilitator-Token": body["facilitator_token"]}
    joined = client.post(
        f"/sessions/{session_id}/participants/join",
        json={"join_token": body["join_token"], "display_name": "Participant"},
    )
    assert joined.status_code == 200
    participant = joined.json()
    assigned = client.put(
        f"/sessions/{session_id}/participants/{participant['participant_id']}/role",
        json={"role_id": role_id},
        headers=facilitator_headers,
    )
    assert assigned.status_code == 200
    started = client.post(f"/sessions/{session_id}/start", headers=facilitator_headers)
    assert started.status_code == 200
    inject = client.post(
        f"/sessions/{session_id}/injects",
        json={
            "title": "Field assessment",
            "description": "Assess local impact and report back.",
            "payload": {"target_role_ids": [role_id]},
        },
        headers=facilitator_headers,
    )
    assert inject.status_code == 200
    return session_id, facilitator_headers, participant, inject.json()["id"]


def submit_payload(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    session_id, _, participant, inject_id = start_session()
    response = client.post(
        f"/sessions/{session_id}/injects/{inject_id}/decisions",
        json={"participant_id": participant["participant_id"], "decision_payload": payload},
        headers={"X-Participant-Token": participant["participant_token"]},
    )
    return response.status_code, response.json()


def test_valid_lego_decision_payload_is_accepted_and_round_trips() -> None:
    payload = lego_payload()

    status, body = submit_payload(payload)

    assert status == 200
    assert body["decision_payload"] == payload
    assert body["decision_payload"]["blocks"][2]["data"]["lat"] == 47.12345
    assert body["decision_payload"]["links"][1]["relation"] == "supports"
    assert body["decision_payload"]["metadata"]["knowledge_scope"] == "participant_report"


def test_legacy_opaque_payload_remains_supported_without_conversion() -> None:
    payload = legacy_payload()

    status, body = submit_payload(payload)

    assert status == 200
    assert body["decision_payload"] == payload
    assert body["decision_payload"]["kind"] == "structured_decision_placeholder"


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "lego_decision", "blocks": [lego_payload()["blocks"][0]]},
        {**lego_payload(), "schema_version": "participant-decision-lego-0.9"},
        {**lego_payload(), "kind": "free_text"},
        {**lego_payload(), "blocks": []},
        {
            **lego_payload(),
            "blocks": [lego_payload()["blocks"][0], lego_payload()["blocks"][0]],
        },
        {
            **lego_payload(),
            "blocks": [{"block_type": "action", "label": "Missing block id", "data": {}}],
        },
        {
            **lego_payload(),
            "blocks": [{"block_id": "missing-type", "label": "Missing block type", "data": {}}],
        },
        {
            **lego_payload(),
            "blocks": [
                {
                    "block_id": "unknown-type",
                    "block_type": "drone_strike",
                    "label": "Unknown type",
                    "data": {},
                }
            ],
        },
        {
            **lego_payload(),
            "links": [
                {
                    "link_id": "bad-link",
                    "from_block_id": "task-1",
                    "to_block_id": "missing-block",
                    "relation": "then",
                }
            ],
        },
        {**lego_payload(), "metadata": {"system_truth": {"hidden_location": "secret"}}},
        {**lego_payload(), "metadata": {"nested": {"target_role_ids": ["role-secret"]}}},
    ],
)
def test_invalid_lego_decision_payload_returns_422(payload: dict[str, object]) -> None:
    status, body = submit_payload(payload)

    assert status == 422
    assert "Invalid LEGO decision payload" in str(body["detail"])

def test_invalid_lego_payload_error_does_not_echo_hidden_metadata_values() -> None:
    payload = {
        **lego_payload(),
        "metadata": {"system_truth": {"exact_location": "SECRET-LOCATION-42"}},
    }

    status, body = submit_payload(payload)

    assert status == 422
    assert "Invalid LEGO decision payload" in str(body["detail"])
    assert "system_truth" in str(body["detail"])
    assert "SECRET-LOCATION-42" not in str(body["detail"])