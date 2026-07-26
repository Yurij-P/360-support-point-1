from typing import Any, AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from tps360.simulation.services.event_broadcaster import (
    SessionEvent,
    SessionEventType,
    broadcaster,
)

router = APIRouter(prefix="/events", tags=["events"])


class SessionEventResponse(BaseModel):
    id: str
    session_id: str
    event_type: SessionEventType
    payload: dict[str, Any]
    target_role_id: str | None
    timestamp_round: int
    timestamp_iso: str



def _to_event_response(event: SessionEvent) -> SessionEventResponse:
    return SessionEventResponse(
        id=event.id,
        session_id=event.session_id,
        event_type=event.event_type,
        payload=event.payload,
        target_role_id=event.target_role_id,
        timestamp_round=event.timestamp_round,
        timestamp_iso=event.timestamp_iso,
    )


@router.get("/session/{session_id}/history", response_model=list[SessionEventResponse])
def get_session_event_history(
    session_id: str,
    role_id: str | None = Query(default=None),
    since_event_id: str | None = Query(default=None),
) -> list[SessionEventResponse]:
    events = broadcaster.get_events(
        session_id=session_id,
        role_id=role_id,
        since_event_id=since_event_id,
    )
    return [_to_event_response(e) for e in events]


@router.get("/session/{session_id}/stream")
async def stream_session_events(
    session_id: str,
    role_id: str | None = Query(default=None),
) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        async for event in broadcaster.subscribe_stream(session_id=session_id, role_id=role_id):
            resp = _to_event_response(event)
            event_data = json.dumps(resp.model_dump())
            yield f"event: {event.event_type}\ndata: {event_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
