from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.simulation.domain.session import (
    FacilitatedSession,
    SessionJournalEntryType,
    SessionStatus,
)

client = TestClient(app)


def make_active_session() -> tuple[FacilitatedSession, UUID, UUID]:
    session = FacilitatedSession(
        community_id=uuid4(),
        facilitator_name="Facilitator",
        player_capacity=1,
        facilitator_token_digest=FacilitatedSession.digest_facilitator_token(
            "facilitator-token"
        ),
    )
    participant = session.join("Player 1")
    role_id = uuid4()
    session.assign_role(participant.id, role_id)
    session.start()
    return session, participant.id, role_id


def start_api_session() -> tuple[str, dict[str, str], str, str]:
    created = client.post(
        "/sessions",
        json={
            "community_id": str(uuid4()),
            "facilitator_name": "Facilitator",
            "player_capacity": 1,
        },
    )
    assert created.status_code == 200
    session_id = created.json()["id"]
    headers = {"X-Facilitator-Token": created.json()["facilitator_token"]}
    joined = client.post(
        f"/sessions/{session_id}/participants",
        json={"display_name": "Player 1"},
    )
    assert joined.status_code == 200
    participant_id = joined.json()["id"]
    role_id = str(uuid4())
    assigned = client.put(
        f"/sessions/{session_id}/participants/{participant_id}/role",
        json={"role_id": role_id},
        headers=headers,
    )
    assert assigned.status_code == 200
    started = client.post(f"/sessions/{session_id}/start", headers=headers)
    assert started.status_code == 200
    return session_id, headers, participant_id, role_id


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

    decision = session.submit_decision(
        inject.id,
        participant_id,
        "Switch to reserve line",
        "Fastest pressure restoration",
    )

    assert decision.participant_id == participant_id
    assert decision.role_id == role_id
    assert decision.inject_id == inject.id
    assert session.journal[-1].type is SessionJournalEntryType.DECISION_SUBMITTED
    assert session.journal[-1].decision_id == decision.id


def test_participant_cannot_submit_duplicate_decision_for_same_inject() -> None:
    session, participant_id, _ = make_active_session()
    inject = session.send_inject("Pressure drop", "Main line pressure dropped")
    session.submit_decision(inject.id, participant_id, "Switch to reserve line")

    with pytest.raises(DomainRuleViolation, match="already submitted"):
        session.submit_decision(inject.id, participant_id, "Send water trucks")


def test_decision_requires_existing_participant_and_inject() -> None:
    session, participant_id, _ = make_active_session()

    with pytest.raises(NotFoundError, match="Inject"):
        session.submit_decision(uuid4(), participant_id, "Switch to reserve line")

    inject = session.send_inject("Pressure drop", "Main line pressure dropped")
    with pytest.raises(NotFoundError, match="Participant"):
        session.submit_decision(inject.id, uuid4(), "Switch to reserve line")


def test_facilitator_completes_active_session_and_blocks_later_actions() -> None:
    session, _, _ = make_active_session()

    session.complete()

    assert session.status is SessionStatus.COMPLETED
    assert session.journal[-1].type is SessionJournalEntryType.SESSION_COMPLETED
    with pytest.raises(DomainRuleViolation, match="active session"):
        session.send_inject("Late inject", "Should be blocked")


def test_active_session_api_flow() -> None:
    session_id, headers, participant_id, role_id = start_api_session()

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
            "selected_action": "Switch to reserve line",
            "rationale": "Fastest pressure restoration",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["participant_id"] == participant_id
    assert decision.json()["role_id"] == role_id

    duplicate = client.post(
        f"/sessions/{session_id}/injects/{inject_id}/decisions",
        json={
            "participant_id": participant_id,
            "selected_action": "Send water trucks",
        },
    )
    assert duplicate.status_code == 409

    journal = client.get(f"/sessions/{session_id}/journal")
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
    session_id, headers, _, _ = start_api_session()

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
    session_id, headers, participant_id, _ = start_api_session()
    inject = client.post(
        f"/sessions/{session_id}/injects",
        json={"title": "Pressure drop", "description": "Main line pressure dropped"},
        headers=headers,
    )

    unknown_inject = client.post(
        f"/sessions/{session_id}/injects/{uuid4()}/decisions",
        json={"participant_id": participant_id, "selected_action": "Switch"},
    )
    unknown_participant = client.post(
        f"/sessions/{session_id}/injects/{inject.json()['id']}/decisions",
        json={"participant_id": str(uuid4()), "selected_action": "Switch"},
    )

    assert unknown_inject.status_code == 404
    assert unknown_participant.status_code == 404
