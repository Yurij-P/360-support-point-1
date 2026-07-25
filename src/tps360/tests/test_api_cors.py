from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def test_participant_origin_is_allowed_without_credentials() -> None:
    response = client.options(
        "/sessions/session-1/participant",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Participant-Token",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"
    assert response.headers.get("access-control-allow-credentials") is None


def test_unknown_origin_is_not_allowed() -> None:
    response = client.options(
        "/sessions/session-1/participant",
        headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Participant-Token",
        },
    )
    assert "access-control-allow-origin" not in response.headers