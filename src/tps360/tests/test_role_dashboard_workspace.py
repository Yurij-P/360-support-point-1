from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.services.role_dashboard_service import RoleDashboardService

client = TestClient(app)
SESS = "sess_role_workspace_test_200"


def test_role_workspace_initial_resources() -> None:
    service = RoleDashboardService()
    workspace = service.get_role_workspace(session_id=SESS, role_id="head_of_emergency")

    assert workspace.role_id == "head_of_emergency"
    assert "fire_trucks" in workspace.initial_resources
    assert workspace.initial_resources["fire_trucks"] == Decimal("10")
    assert workspace.available_resources["fire_trucks"] == Decimal("10")
    assert workspace.reserved_resources["fire_trucks"] == Decimal("0")


def test_submit_lego_decision_card_allocates_and_locks_resources() -> None:
    service = RoleDashboardService()
    card = service.submit_lego_decision_card(
        session_id=SESS,
        role_id="head_of_emergency",
        action_type="EXTINGUISH_FIRE",
        target_facility_id="osm_substation_44",
        allocated_resources={"fire_trucks": Decimal("6"), "fuel_liters": Decimal("2000")},
        allocated_personnel=15,
        custom_instructions="Гасіння пожежі на трансформаторній підстанції",
        current_round=1,
    )

    assert card.card_id.startswith("card_")
    assert card.action_type == "EXTINGUISH_FIRE"
    assert card.status == "PENDING_ROUND_EXECUTION"

    workspace = service.get_role_workspace(session_id=SESS, role_id="head_of_emergency")
    assert workspace.available_resources["fire_trucks"] == Decimal("4")
    assert workspace.reserved_resources["fire_trucks"] == Decimal("6")
    assert workspace.available_resources["fuel_liters"] == Decimal("3000")
    assert len(workspace.pending_lego_cards) == 1


def test_100_percent_resource_exhaustion_supported() -> None:
    service = RoleDashboardService()
    # Allocate 100% (10 out of 10 fire_trucks)
    service.submit_lego_decision_card(
        session_id=SESS,
        role_id="head_of_emergency",
        action_type="CONTAIN",
        target_facility_id="osm_oil_depot_1",
        allocated_resources={"fire_trucks": Decimal("10")},
    )

    workspace = service.get_role_workspace(session_id=SESS, role_id="head_of_emergency")
    assert workspace.available_resources["fire_trucks"] == Decimal("0")
    assert workspace.reserved_resources["fire_trucks"] == Decimal("10")

    # Attempting to allocate more fails with DomainRuleViolation
    with pytest.raises(DomainRuleViolation, match="Insufficient 'fire_trucks' resources"):
        service.submit_lego_decision_card(
            session_id=SESS,
            role_id="head_of_emergency",
            action_type="EVACUATE",
            target_facility_id="osm_zone_2",
            allocated_resources={"fire_trucks": Decimal("1")},
        )


def test_inter_role_oms_resource_transfer() -> None:
    service = RoleDashboardService()
    # Chief Utility transfers 3 backup_generators to Chief Medical Officer
    transfer = service.transfer_resources_oms(
        session_id=SESS,
        sender_role_id="chief_utility_officer",
        recipient_role_id="chief_medical_officer",
        resources={"backup_generators": Decimal("3")},
        authorization_note="Розпорядження ОМС для живлення медустанови",
    )

    assert transfer.transfer_id.startswith("trans_")
    assert transfer.resources["backup_generators"] == Decimal("3")

    utility_ws = service.get_role_workspace(SESS, "chief_utility_officer")
    medical_ws = service.get_role_workspace(SESS, "chief_medical_officer")

    assert utility_ws.available_resources["backup_generators"] == Decimal("7")
    assert medical_ws.available_resources["backup_generators"] == Decimal("7")  # 4 initial + 3 transferred!


def test_resolve_round_execution_clears_reserved_resources() -> None:
    service = RoleDashboardService()
    service.submit_lego_decision_card(
        session_id=SESS,
        role_id="chief_medical_officer",
        action_type="DEPLOY_SHELTER",
        target_facility_id="osm_hospital_99",
        allocated_resources={"generators": Decimal("2")},
    )

    outcomes = service.resolve_round_execution(session_id=SESS, round_number=1)
    assert len(outcomes) == 1
    assert outcomes[0]["status"] == "EXECUTED_IN_ROUND"

    workspace = service.get_role_workspace(session_id=SESS, role_id="chief_medical_officer")
    assert workspace.reserved_resources["generators"] == Decimal("0")
    assert len(workspace.pending_lego_cards) == 0


def test_role_workspace_api_endpoints() -> None:
    sess_id = "sess_api_role_workspace_888"

    # Get Workspace
    response = client.get(f"/sessions/{sess_id}/role-workspace?role_id=head_of_emergency")
    assert response.status_code == 200
    w_data = response.json()
    assert w_data["role_id"] == "head_of_emergency"
    assert "fire_trucks" in w_data["available_resources"]

    # Submit LEGO Card
    card_resp = client.post(
        f"/sessions/{sess_id}/lego-decisions",
        json={
            "role_id": "head_of_emergency",
            "action_type": "EVACUATE",
            "target_facility_id": "osm_school_12",
            "allocated_resources": {"fire_trucks": "2"},
            "allocated_personnel": 10,
            "custom_instructions": "Евакуація населення",
        },
    )
    assert card_resp.status_code == 200
    c_data = card_resp.json()
    assert c_data["action_type"] == "EVACUATE"

    # Transfer Resources OMS
    trans_resp = client.post(
        f"/sessions/{sess_id}/resource-transfers",
        json={
            "sender_role_id": "head_of_emergency",
            "recipient_role_id": "chief_police_officer",
            "resources": {"fuel_liters": "500"},
            "authorization_note": "Розпорядження ОМС для патрулювання",
        },
    )
    assert trans_resp.status_code == 200
    t_data = trans_resp.json()
    assert t_data["sender_role_id"] == "head_of_emergency"

    # Query AI Resource Estimate
    ai_resp = client.get(f"/sessions/{sess_id}/ai-resource-estimate?action_type=EXTINGUISH_FIRE&hazard_radius_km=1.5")
    assert ai_resp.status_code == 200
    ai_data = ai_resp.json()
    assert "ai_recommended_resources" in ai_data
    assert "fire_trucks" in ai_data["ai_recommended_resources"]

