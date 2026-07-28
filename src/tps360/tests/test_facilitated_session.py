from uuid import uuid4

import pytest

from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.simulation.domain.session import FacilitatedSession, RoleProfile, SessionStatus

ROLE_ID = uuid4()

def make_session(capacity: int = 2) -> FacilitatedSession:
    return FacilitatedSession(
        community_id=str(uuid4()),
        facilitator_name="Р¤Р°СЃРёР»С–С‚Р°С‚РѕСЂ",
        player_capacity=capacity,
        facilitator_token_digest=FacilitatedSession.digest_facilitator_token(
            "facilitator-token"
        ),
        role_profiles=[
            RoleProfile(
                role_id=ROLE_ID,
                title="Test role",
                category="Test category",
                briefing="Test briefing",
            )
        ],
    )


def test_player_joins_lobby_without_role() -> None:
    session = make_session()
    participant = session.join("Р“СЂР°РІРµС†СЊ 1")

    assert participant.role_id is None
    assert session.status is SessionStatus.LOBBY


def test_facilitator_assigns_role_and_session_becomes_ready() -> None:
    session = make_session()
    participant = session.join("Р“СЂР°РІРµС†СЊ 1")

    assigned = session.assign_role(participant.id, ROLE_ID)

    assert assigned.role_id is not None
    assert session.status is SessionStatus.READY


def test_new_player_can_join_ready_session_and_returns_it_to_lobby() -> None:
    session = make_session()
    first = session.join("Р“СЂР°РІРµС†СЊ 1")
    session.assign_role(first.id, ROLE_ID)

    second = session.join("Р“СЂР°РІРµС†СЊ 2")

    assert second.role_id is None
    assert session.status is SessionStatus.LOBBY


def test_session_cannot_start_with_unassigned_player() -> None:
    session = make_session()
    session.join("Р“СЂР°РІРµС†СЊ 1")

    with pytest.raises(DomainRuleViolation):
        session.start()


def test_session_starts_after_all_connected_players_have_roles() -> None:
    session = make_session()
    first = session.join("Р“СЂР°РІРµС†СЊ 1")
    second = session.join("Р“СЂР°РІРµС†СЊ 2")
    session.assign_role(first.id, ROLE_ID)
    session.assign_role(second.id, ROLE_ID)

    session.start()

    assert session.status is SessionStatus.ACTIVE


def test_active_session_cannot_be_started_again() -> None:
    session = make_session()
    participant = session.join("Р“СЂР°РІРµС†СЊ 1")
    session.assign_role(participant.id, ROLE_ID)
    session.start()

    with pytest.raises(DomainRuleViolation, match="Only a ready session"):
        session.start()


def test_session_rejects_players_above_facilitator_capacity() -> None:
    session = make_session(capacity=1)
    session.join("Р“СЂР°РІРµС†СЊ 1")

    with pytest.raises(DomainRuleViolation):
        session.join("Р“СЂР°РІРµС†СЊ 2")


def test_role_cannot_be_assigned_to_unknown_participant() -> None:
    session = make_session()

    with pytest.raises(NotFoundError):
        session.assign_role(uuid4(), uuid4())
