from uuid import uuid4

from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.session import (
    CrisisCondition,
    CrisisDefinition,
    FacilitatedSession,
    SessionStatus,
)

client = TestClient(app)


# ── Domain unit tests ─────────────────────────────────────────────────────────

def _make_session(**kwargs: object) -> FacilitatedSession:
    return FacilitatedSession(
        community_id=uuid4(),
        facilitator_name="Test",
        player_capacity=5,
        facilitator_token_digest=FacilitatedSession.digest_facilitator_token("tok"),
        **kwargs,  # type: ignore[arg-type]
    )


def _definition(**kwargs: object) -> CrisisDefinition:
    return CrisisDefinition(
        title="Ракетний удар по підстанції",
        category="military_political",
        primary_hazard="missile_strike",
        secondary_hazards=["power_grid_damage"],
        potential_impacts=["electricity_loss", "evacuation_required"],
        description="Удар по трансформаторній підстанції о 03:00",
        **kwargs,  # type: ignore[arg-type]
    )


def test_define_crisis_sets_definition_on_lobby_session() -> None:
    session = _make_session()
    defn = _definition()
    result = session.define_crisis(defn)
    assert result is defn
    assert session.crisis_definition is defn


def test_define_crisis_replaces_existing_definition() -> None:
    session = _make_session()
    session.define_crisis(_definition())
    second = CrisisDefinition(
        title="Second",
        category="military_political",
        primary_hazard="missile_strike",
        description="Second definition",
    )
    session.define_crisis(second)
    assert session.crisis_definition is not None
    assert session.crisis_definition.title == "Second"


def test_define_crisis_rejected_when_session_active() -> None:
    import pytest
    session = _make_session(status=SessionStatus.ACTIVE)
    with pytest.raises(DomainRuleViolation, match="before the session starts"):
        session.define_crisis(_definition())


def test_add_crisis_condition_appends_to_definition() -> None:
    session = _make_session()
    session.define_crisis(_definition())
    cond = CrisisCondition(description="Відключення в 3 районах", value="3", unit="districts")
    result = session.add_crisis_condition(cond)
    assert result is cond
    assert len(session.crisis_definition.conditions) == 1  # type: ignore[union-attr]


def test_add_crisis_condition_rejected_without_definition() -> None:
    import pytest
    session = _make_session()
    with pytest.raises(DomainRuleViolation, match="Crisis must be defined"):
        session.add_crisis_condition(CrisisCondition(description="test"))


def test_add_crisis_condition_rejects_duplicate_id() -> None:
    import pytest
    session = _make_session()
    session.define_crisis(_definition())
    cond_id = uuid4()
    session.add_crisis_condition(CrisisCondition(id=cond_id, description="First"))
    with pytest.raises(DomainRuleViolation, match="already exists"):
        session.add_crisis_condition(CrisisCondition(id=cond_id, description="Duplicate"))


# ── API endpoint tests ────────────────────────────────────────────────────────

def _create_session() -> dict[str, str]:
    resp = client.post(
        "/sessions",
        json={"community_id": str(uuid4()), "facilitator_name": "Facilitator", "player_capacity": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    return {"session_id": body["id"], "facilitator_token": body["facilitator_token"]}


def test_get_crisis_returns_null_when_not_defined() -> None:
    data = _create_session()
    resp = client.get(f"/sessions/{data['session_id']}/crisis")
    assert resp.status_code == 200
    assert resp.json() is None


def test_define_crisis_requires_facilitator_token() -> None:
    data = _create_session()
    resp = client.post(
        f"/sessions/{data['session_id']}/crisis/define",
        json={"title": "t", "category": "military_political", "primary_hazard": "missile_strike", "description": "d"},
    )
    assert resp.status_code == 401


def test_define_crisis_rejects_invalid_category() -> None:
    data = _create_session()
    resp = client.post(
        f"/sessions/{data['session_id']}/crisis/define",
        json={"title": "t", "category": "invalid_cat", "primary_hazard": "missile_strike", "description": "d"},
        headers={"X-Facilitator-Token": data["facilitator_token"]},
    )
    assert resp.status_code == 422


def test_define_crisis_and_get_returns_definition() -> None:
    data = _create_session()
    resp = client.post(
        f"/sessions/{data['session_id']}/crisis/define",
        json={
            "title": "Ракетний удар",
            "category": "military_political",
            "primary_hazard": "missile_strike",
            "secondary_hazards": ["power_grid_damage"],
            "potential_impacts": ["electricity_loss"],
            "description": "Удар о 03:00",
            "affected_area_description": "Центральний район",
        },
        headers={"X-Facilitator-Token": data["facilitator_token"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Ракетний удар"
    assert body["category"] == "military_political"
    assert body["primary_hazard"] == "missile_strike"
    assert body["secondary_hazards"] == ["power_grid_damage"]
    assert body["conditions"] == []

    get_resp = client.get(f"/sessions/{data['session_id']}/crisis")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Ракетний удар"


def test_add_crisis_condition_without_prior_definition_returns_409() -> None:
    data = _create_session()
    resp = client.post(
        f"/sessions/{data['session_id']}/crisis/add-condition",
        json={"description": "Відключення"},
        headers={"X-Facilitator-Token": data["facilitator_token"]},
    )
    assert resp.status_code == 409


def test_add_crisis_condition_appends_and_persists() -> None:
    data = _create_session()
    client.post(
        f"/sessions/{data['session_id']}/crisis/define",
        json={"title": "Удар", "category": "military_political", "primary_hazard": "missile_strike", "description": "d"},
        headers={"X-Facilitator-Token": data["facilitator_token"]},
    )
    resp = client.post(
        f"/sessions/{data['session_id']}/crisis/add-condition",
        json={"description": "Відключення в 3 районах", "value": "3", "unit": "districts", "confirmed": True},
        headers={"X-Facilitator-Token": data["facilitator_token"]},
    )
    assert resp.status_code == 200
    cond = resp.json()
    assert cond["description"] == "Відключення в 3 районах"
    assert cond["value"] == "3"
    assert cond["confirmed"] is True

    get_resp = client.get(f"/sessions/{data['session_id']}/crisis")
    assert len(get_resp.json()["conditions"]) == 1
