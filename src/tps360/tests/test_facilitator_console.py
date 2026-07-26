from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.simulation.services.facilitator_console_service import (
    FacilitatorConsoleService,
)

client = TestClient(app)
SESS = "sess_facilitator_console_test_300"


def test_generate_5_future_lifecycle_variants() -> None:
    service = FacilitatorConsoleService()
    variants = service.generate_5_future_lifecycle_variants(
        session_id=SESS,
        crisis_type="Ракетний удар по нафтобазі",
        current_round=1,
    )

    assert len(variants) == 5
    variant_ids = [v.variant_id for v in variants]
    assert "BEST_CASE_CONTAINED" in variant_ids
    assert "MODERATE_STABLE" in variant_ids
    assert "ESCALATION_HAZARD" in variant_ids
    assert "INFRASTRUCTURE_COLLAPSE" in variant_ids
    assert "WORST_CASE_CASCADE" in variant_ids


def test_facilitator_console_read_model() -> None:
    service = FacilitatorConsoleService()
    console = service.get_facilitator_console(
        session_id=SESS,
        current_round=2,
        crisis_type="Пожежа на підстанції",
        connected_participants=3,
        assigned_roles=3,
        pending_cards_count=2,
    )

    assert console.session_id == SESS
    assert console.current_round == 2
    assert console.connected_participants_count == 3
    assert len(console.future_projections_5_variants) == 5


def test_approve_ai_proposal_and_advance_round() -> None:
    service = FacilitatorConsoleService()
    approval = service.approve_ai_proposal(
        session_id=SESS,
        variant_id="ESCALATION_HAZARD",
        custom_title="Загроза поширення вогню",
        current_round=1,
    )

    assert approval["variant_id"] == "ESCALATION_HAZARD"
    assert approval["approved_title"] == "Загроза поширення вогню"

    advance = service.advance_session_round(session_id=SESS, current_round=1)
    assert advance["previous_round"] == 1
    assert advance["new_round"] == 2
    assert advance["status"] == "ROUND_ADVANCED"


def test_facilitator_console_api_endpoints() -> None:
    sess_id = "sess_api_facilitator_777"

    # Get Master Console
    console_resp = client.get(f"/sessions/{sess_id}/facilitator-console")
    assert console_resp.status_code == 200
    c_data = console_resp.json()
    assert c_data["session_id"] == sess_id
    assert len(c_data["future_projections_5_variants"]) == 5

    # Get 5 Future Projections
    proj_resp = client.get(f"/sessions/{sess_id}/future-projections?current_round=1")
    assert proj_resp.status_code == 200
    p_data = proj_resp.json()
    assert len(p_data) == 5

    # Approve AI Proposal
    app_resp = client.post(
        f"/sessions/{sess_id}/injects/approve-ai-proposal",
        json={"variant_id": "BEST_CASE_CONTAINED", "custom_title": "Успішна локалізація"},
    )
    assert app_resp.status_code == 200
    a_data = app_resp.json()
    assert a_data["approved_title"] == "Успішна локалізація"

    # Advance Round
    adv_resp = client.post(f"/sessions/{sess_id}/rounds/advance?current_round=1")
    assert adv_resp.status_code == 200
    ad_data = adv_resp.json()
    assert ad_data["new_round"] == 2
