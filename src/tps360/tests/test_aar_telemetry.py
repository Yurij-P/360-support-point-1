from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.simulation.services.aar_telemetry_service import (
    AARTelemetryService,
)

client = TestClient(app)
SESS = "sess_aar_telemetry_test_900"


def test_record_round_telemetry_and_aar_report() -> None:
    service = AARTelemetryService()
    service.record_round_telemetry(
        session_id=SESS,
        round_number=1,
        mitigation_pct=45.0,
        role_capabilities={"head_of_emergency": 90.0},
        resource_levels={"head_of_emergency": {"fire_trucks": 8.0}},
        cognitive_stress_indexes={"head_of_emergency": 15.0},
    )

    telemetry = service.get_session_telemetry(SESS)
    assert len(telemetry) == 1
    assert telemetry[0].round_number == 1
    assert telemetry[0].mitigation_pct == 45.0

    report = service.generate_aar_report(session_id=SESS, total_rounds=2)
    assert report.session_id == SESS
    assert report.final_status == "COMPLETED_SUCCESS"
    assert len(report.ai_learning_insights) > 0


def test_participant_experience_memory() -> None:
    service = AARTelemetryService()
    p_id = "user_commander_123"

    rec1 = service.record_participant_experience(participant_id=p_id, community_id="verkhovyna")
    assert rec1.sessions_played == 1

    rec2 = service.record_participant_experience(participant_id=p_id, community_id="verkhovyna")
    assert rec2.sessions_played == 2


def test_aar_telemetry_api_endpoints() -> None:
    sess_id = "sess_aar_api_888"

    # Get AAR Report
    aar_resp = client.get(f"/sessions/{sess_id}/aar-report")
    assert aar_resp.status_code == 200
    aar_data = aar_resp.json()
    assert aar_data["session_id"] == sess_id
    assert aar_data["final_status"] == "COMPLETED_SUCCESS"

    # Get Session Telemetry
    tel_resp = client.get(f"/sessions/{sess_id}/telemetry")
    assert tel_resp.status_code == 200
    assert isinstance(tel_resp.json(), list)

    # Get Participant Experience Record
    exp_resp = client.get("/sessions/participants/user_test_55/experience-record")
    assert exp_resp.status_code == 200
    e_data = exp_resp.json()
    assert e_data["participant_id"] == "user_test_55"
