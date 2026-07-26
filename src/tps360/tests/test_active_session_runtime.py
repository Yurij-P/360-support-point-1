from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.simulation.domain.session import (
    FacilitatedSession,
    RoleProfile,
    SessionJournalEntryType,
    SessionStatus,
)

client = TestClient(app)

def decision_payload(
    title: str = "Act",
    description: str = "Submit a structured placeholder decision.",
    rationale: str = "Because the participant selected this response.",
) -> dict[str, object]:
    return {
        "schema_version": "participant-decision-draft-0.1",
        "kind": "structured_decision_placeholder",
        "blocks": [],
        "notes": {
            "title": title,
            "description": description,
            "rationale": rationale,
        },
    }


def make_active_session() -> tuple[FacilitatedSession, UUID, UUID]:
    role_id = uuid4()
    session = FacilitatedSession(
        community_id=uuid4(),
        facilitator_name="Facilitator",
        player_capacity=1,
        facilitator_token_digest=FacilitatedSession.digest_facilitator_token(
            "facilitator-token"
        ),
        role_profiles=[
            RoleProfile(
                role_id=role_id,
                title="Test role",
                category="Test category",
                briefing="Test briefing",
            )
        ],
    )
    participant = session.join("Player 1")
    session.assign_role(participant.id, role_id)
    session.start()
    return session, participant.id, role_id


def start_api_session() -> tuple[str, dict[str, str], str, str, str]:
    role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Facilitator",
            "player_capacity": 1,
            "role_profiles": [{
                "role_id": role_id,
                "title": "Test role",
                "category": "Test category",
                "briefing": "Test briefing",
            }],
        },
    )
    assert created.status_code == 200
    session_id = created.json()["id"]
    headers = {"X-Facilitator-Token": created.json()["facilitator_token"]}
    joined = client.post(
        f"/sessions/{session_id}/participants/join",
        json={
            "display_name": "Player 1",
            "join_token": created.json()["join_token"],
        },
    )
    assert joined.status_code == 200
    participant_id = joined.json()["participant_id"]
    participant_token = joined.json()["participant_token"]
    assigned = client.put(
        f"/sessions/{session_id}/participants/{participant_id}/role",
        json={"role_id": role_id},
        headers=headers,
    )
    assert assigned.status_code == 200
    started = client.post(f"/sessions/{session_id}/start", headers=headers)
    assert started.status_code == 200
    return session_id, headers, participant_id, participant_token, role_id


def test_facilitator_sends_inject_only_during_active_session() -> None:
    session, _, _ = make_active_session()

    inject = session.send_inject("Pressure drop", "Main line pressure dropped")

    assert inject in session.injects
    assert session.journal[-1].type is SessionJournalEntryType.INJECT_SENT
    assert session.journal[-1].inject_id == inject.id


def test_injects_require_active_session() -> None:
    session = FacilitatedSession(
        community_id=uuid4(),
        facilitator_name="Facilitator",
        player_capacity=1,
        facilitator_token_digest=FacilitatedSession.digest_facilitator_token("token"),
    )

    with pytest.raises(DomainRuleViolation, match="active session"):
        session.send_inject("Pressure drop", "Main line pressure dropped")


def test_participant_decision_records_role_and_journal_entry() -> None:
    session, participant_id, role_id = make_active_session()
    inject = session.send_inject("Pressure drop", "Main line pressure dropped")

    payload = decision_payload(
        "Switch to reserve line",
        "Use the reserve line for pressure restoration.",
        "Fastest pressure restoration",
    )
    decision = session.submit_decision(inject.id, participant_id, payload)

    assert decision.participant_id == participant_id
    assert decision.role_id == role_id
    assert decision.inject_id == inject.id
    assert decision.decision_payload == payload
    assert session.journal[-1].type is SessionJournalEntryType.DECISION_SUBMITTED
    assert session.journal[-1].decision_id == decision.id


def test_participant_cannot_submit_duplicate_decision_for_same_inject() -> None:
    session, participant_id, _ = make_active_session()
    inject = session.send_inject("Pressure drop", "Main line pressure dropped")
    session.submit_decision(inject.id, participant_id, decision_payload("Switch to reserve line"))

    with pytest.raises(DomainRuleViolation, match="already submitted"):
        session.submit_decision(inject.id, participant_id, decision_payload("Send water trucks"))


def test_decision_requires_existing_participant_and_inject() -> None:
    session, participant_id, _ = make_active_session()

    with pytest.raises(NotFoundError, match="Inject"):
        session.submit_decision(uuid4(), participant_id, decision_payload("Switch to reserve line"))

    inject = session.send_inject("Pressure drop", "Main line pressure dropped")
    with pytest.raises(NotFoundError, match="Participant"):
        session.submit_decision(inject.id, uuid4(), decision_payload("Switch to reserve line"))


def test_facilitator_completes_active_session_and_blocks_later_actions() -> None:
    session, _, _ = make_active_session()

    session.complete()

    assert session.status is SessionStatus.COMPLETED
    assert session.journal[-1].type is SessionJournalEntryType.SESSION_COMPLETED
    with pytest.raises(DomainRuleViolation, match="active session"):
        session.send_inject("Late inject", "Should be blocked")


def test_active_session_api_flow() -> None:
    session_id, headers, participant_id, participant_token, role_id = start_api_session()

    inject = client.post(
        f"/sessions/{session_id}/injects",
        json={
            "title": "Pressure drop",
            "description": "Main line pressure dropped",
            "payload": {"severity": "critical"},
        },
        headers=headers,
    )
    assert inject.status_code == 200
    inject_id = inject.json()["id"]

    decision = client.post(
        f"/sessions/{session_id}/injects/{inject_id}/decisions",
        json={
            "participant_id": participant_id,
            "decision_payload": decision_payload(
                "Switch to reserve line",
                "Use the reserve line for pressure restoration.",
                "Fastest pressure restoration",
            ),
        },
        headers={"X-Participant-Token": participant_token},
    )
    assert decision.status_code == 200
    assert decision.json()["participant_id"] == participant_id
    assert decision.json()["role_id"] == role_id
    assert decision.json()["decision_payload"]["kind"] == "structured_decision_placeholder"
    assert "selected_action" not in decision.json()

    duplicate = client.post(
        f"/sessions/{session_id}/injects/{inject_id}/decisions",
        json={
            "participant_id": participant_id,
            "decision_payload": decision_payload("Send water trucks"),
        },
        headers={"X-Participant-Token": participant_token},
    )
    assert duplicate.status_code == 409

    journal = client.get(f"/sessions/{session_id}/journal", headers=headers)
    assert journal.status_code == 200
    assert [entry["type"] for entry in journal.json()] == [
        "session_started",
        "inject_sent",
        "decision_submitted",
    ]

    completed = client.post(f"/sessions/{session_id}/complete", headers=headers)
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["journal"][-1]["type"] == "session_completed"


def test_facilitator_token_protects_inject_and_completion() -> None:
    session_id, headers, _, _, _ = start_api_session()

    missing = client.post(
        f"/sessions/{session_id}/injects",
        json={"title": "Pressure drop", "description": "Main line pressure dropped"},
    )
    invalid = client.post(
        f"/sessions/{session_id}/complete",
        headers={"X-Facilitator-Token": "wrong"},
    )
    authorized = client.post(f"/sessions/{session_id}/complete", headers=headers)

    assert missing.status_code == 401
    assert invalid.status_code == 403
    assert authorized.status_code == 200


def test_decision_for_unknown_participant_or_inject_returns_not_found() -> None:
    session_id, headers, participant_id, participant_token, _ = start_api_session()
    inject = client.post(
        f"/sessions/{session_id}/injects",
        json={"title": "Pressure drop", "description": "Main line pressure dropped"},
        headers=headers,
    )

    unknown_inject = client.post(
        f"/sessions/{session_id}/injects/{uuid4()}/decisions",
        json={"participant_id": participant_id, "decision_payload": decision_payload("Switch")},
        headers={"X-Participant-Token": participant_token},
    )
    unknown_participant = client.post(
        f"/sessions/{session_id}/injects/{inject.json()['id']}/decisions",
        json={"participant_id": str(uuid4()), "decision_payload": decision_payload("Switch")},
        headers={"X-Participant-Token": participant_token},
    )

    assert unknown_inject.status_code == 404
    assert unknown_participant.status_code == 403


def start_two_participant_api_session() -> tuple[str, dict[str, str], dict[str, str], dict[str, str]]:
    first_role_id = str(uuid4())
    second_role_id = str(uuid4())
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Facilitator",
            "player_capacity": 2,
            "role_profiles": [
                {
                    "role_id": first_role_id,
                    "title": "Coordinator",
                    "category": "Leadership",
                    "briefing": "Coordinate response.",
                },
                {
                    "role_id": second_role_id,
                    "title": "Observer",
                    "category": "Monitoring",
                    "briefing": "Monitor response.",
                },
            ],
        },
    )
    assert created.status_code == 200
    body = created.json()
    session_id = body["id"]
    headers = {"X-Facilitator-Token": body["facilitator_token"]}
    first_joined = client.post(
        f"/sessions/{session_id}/participants/join",
        json={"join_token": body["join_token"], "display_name": "Participant One"},
    )
    second_joined = client.post(
        f"/sessions/{session_id}/participants/join",
        json={"join_token": body["join_token"], "display_name": "Participant Two"},
    )
    assert first_joined.status_code == 200
    assert second_joined.status_code == 200
    first = first_joined.json()
    second = second_joined.json()
    assert client.put(
        f"/sessions/{session_id}/participants/{first['participant_id']}/role",
        json={"role_id": first_role_id},
        headers=headers,
    ).status_code == 200
    assert client.put(
        f"/sessions/{session_id}/participants/{second['participant_id']}/role",
        json={"role_id": second_role_id},
        headers=headers,
    ).status_code == 200
    assert client.post(f"/sessions/{session_id}/start", headers=headers).status_code == 200
    first.update({"role_id": first_role_id})
    second.update({"role_id": second_role_id})
    return session_id, headers, first, second


def test_participant_view_returns_allowed_injects_and_only_own_decisions() -> None:
    session_id, headers, first, second = start_two_participant_api_session()
    public_inject = client.post(
        f"/sessions/{session_id}/injects",
        json={"title": "Public", "description": "Visible to all participants"},
        headers=headers,
    )
    role_inject = client.post(
        f"/sessions/{session_id}/injects",
        json={
            "title": "Coordinator only",
            "description": "Visible to coordinator role",
            "payload": {"target_role_ids": [first["role_id"]]},
        },
        headers=headers,
    )
    blocked_inject = client.post(
        f"/sessions/{session_id}/injects",
        json={
            "title": "Observer only",
            "description": "Visible to observer role",
            "payload": {"target_role_ids": [second["role_id"]]},
        },
        headers=headers,
    )
    assert public_inject.status_code == 200
    assert role_inject.status_code == 200
    assert blocked_inject.status_code == 200

    first_decision = client.post(
        f"/sessions/{session_id}/injects/{public_inject.json()['id']}/decisions",
        json={
            "participant_id": first["participant_id"],
            "decision_payload": decision_payload(
                "Open shelter",
                "Open a reserve shelter for residents.",
                "Public inject response",
            ),
        },
        headers={"X-Participant-Token": first["participant_token"]},
    )
    second_decision = client.post(
        f"/sessions/{session_id}/injects/{blocked_inject.json()['id']}/decisions",
        json={
            "participant_id": second["participant_id"],
            "decision_payload": decision_payload("Monitor update"),
        },
        headers={"X-Participant-Token": second["participant_token"]},
    )
    assert first_decision.status_code == 200
    assert second_decision.status_code == 200

    visible = client.get(
        f"/sessions/{session_id}/participant",
        headers={"X-Participant-Token": first["participant_token"]},
    )
    assert visible.status_code == 200
    body = visible.json()
    assert "participants" not in body
    assert "facilitator_token" not in body
    assert {inject["title"] for inject in body["injects"]} == {"Public", "Coordinator only"}
    assert [decision["id"] for decision in body["decisions"]] == [first_decision.json()["id"]]


def test_participant_decision_submit_requires_valid_matching_token() -> None:
    session_id, headers, first, second = start_two_participant_api_session()
    inject = client.post(
        f"/sessions/{session_id}/injects",
        json={"title": "Public", "description": "Visible to all participants"},
        headers=headers,
    )
    assert inject.status_code == 200
    url = f"/sessions/{session_id}/injects/{inject.json()['id']}/decisions"

    assert client.post(url, json={"participant_id": first["participant_id"], "decision_payload": decision_payload("Act")}).status_code == 401
    assert client.post(
        url,
        json={"participant_id": first["participant_id"], "decision_payload": decision_payload("Act")},
        headers={"X-Participant-Token": "invalid"},
    ).status_code == 403
    spoofed = client.post(
        url,
        json={"participant_id": second["participant_id"], "decision_payload": decision_payload("Act")},
        headers={"X-Participant-Token": first["participant_token"]},
    )
    assert spoofed.status_code == 403

    accepted = client.post(
        url,
        json={"participant_id": first["participant_id"], "decision_payload": decision_payload("Act")},
        headers={"X-Participant-Token": first["participant_token"]},
    )
    assert accepted.status_code == 200
    assert accepted.json()["participant_id"] == first["participant_id"]


def test_participant_decision_rejects_foreign_session_token_and_inaccessible_inject() -> None:
    session_id, headers, first, second = start_two_participant_api_session()
    other_session_id, _, other, _ = start_two_participant_api_session()
    role_inject = client.post(
        f"/sessions/{session_id}/injects",
        json={
            "title": "Coordinator only",
            "description": "Visible to coordinator role",
            "payload": {"target_role_ids": [first["role_id"]]},
        },
        headers=headers,
    )
    assert role_inject.status_code == 200
    url = f"/sessions/{session_id}/injects/{role_inject.json()['id']}/decisions"

    foreign = client.post(
        url,
        json={"participant_id": first["participant_id"], "decision_payload": decision_payload("Act")},
        headers={"X-Participant-Token": other["participant_token"]},
    )
    inaccessible = client.post(
        url,
        json={"participant_id": second["participant_id"], "decision_payload": decision_payload("Act")},
        headers={"X-Participant-Token": second["participant_token"]},
    )

    assert other_session_id != session_id
    assert foreign.status_code == 403
    assert inaccessible.status_code == 403


def test_facilitator_journal_contains_participant_decision_submission() -> None:
    session_id, headers, first, _ = start_two_participant_api_session()
    inject = client.post(
        f"/sessions/{session_id}/injects",
        json={"title": "Public", "description": "Visible to all participants"},
        headers=headers,
    )
    decision = client.post(
        f"/sessions/{session_id}/injects/{inject.json()['id']}/decisions",
        json={"participant_id": first["participant_id"], "decision_payload": decision_payload("Act")},
        headers={"X-Participant-Token": first["participant_token"]},
    )
    assert decision.status_code == 200

    journal = client.get(f"/sessions/{session_id}/journal", headers=headers)
    assert journal.status_code == 200
    assert journal.json()[-1]["type"] == "decision_submitted"
    assert journal.json()[-1]["decision_id"] == decision.json()["id"]


def test_facilitator_journal_requires_valid_facilitator_token() -> None:
    session_id, headers, first, _ = start_two_participant_api_session()
    inject = client.post(
        f"/sessions/{session_id}/injects",
        json={"title": "Public", "description": "Visible to all participants"},
        headers=headers,
    )
    assert inject.status_code == 200
    decision = client.post(
        f"/sessions/{session_id}/injects/{inject.json()['id']}/decisions",
        json={"participant_id": first["participant_id"], "decision_payload": decision_payload("Act")},
        headers={"X-Participant-Token": first["participant_token"]},
    )
    assert decision.status_code == 200

    missing = client.get(f"/sessions/{session_id}/journal")
    invalid = client.get(
        f"/sessions/{session_id}/journal",
        headers={"X-Facilitator-Token": "invalid"},
    )
    allowed = client.get(f"/sessions/{session_id}/journal", headers=headers)

    assert missing.status_code == 401
    assert invalid.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()[-1]["type"] == "decision_submitted"
