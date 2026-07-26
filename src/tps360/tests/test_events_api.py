from fastapi.testclient import TestClient

from tps360.api.main import app
from tps360.simulation.services.event_broadcaster import (
    SessionEventType,
    broadcaster,
    create_event,
)

client = TestClient(app)


def test_get_events_history_api() -> None:
    session_id = "session_events_api"
    event = create_event(
        session_id=session_id,
        event_type=SessionEventType.ROUND_PROGRESSED,
        payload={"round": 2},
    )
    broadcaster.publish(event)

    response = client.get(f"/events/session/{session_id}/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["event_type"] == "ROUND_PROGRESSED"
    assert data[0]["payload"] == {"round": 2}


def test_stream_events_api_endpoint_headers() -> None:
    session_id = "session_events_stream"
    response = client.get(f"/events/session/{session_id}/stream")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
