from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def test_cors_headers_for_web_frontend() -> None:
    response = client.options(
        "/api/v1/sessions",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_e2e_frontend_catalog_flow() -> None:
    response = client.get("/api/v1/communities/catalog")
    assert response.status_code == 200
    catalog = response.json()
    assert isinstance(catalog, list)
    assert len(catalog) >= 1


def test_e2e_frontend_session_full_lifecycle_api() -> None:
    session_id = "sess_e2e_web_frontend_777"

    # 1. Fetch Facilitator Console
    fc_resp = client.get(f"/api/v1/sessions/{session_id}/facilitator-console")
    assert fc_resp.status_code == 200

    # 2. Fetch Role Workspace
    rw_resp = client.get(
        f"/api/v1/sessions/{session_id}/role-workspace?role_id=head_of_emergency"
    )
    assert rw_resp.status_code == 200

    # 3. Fetch AAR Report
    aar_resp = client.get(f"/api/v1/sessions/{session_id}/aar-report")
    assert aar_resp.status_code == 200
    assert aar_resp.json()["session_id"] == session_id
