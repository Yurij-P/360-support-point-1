
from tps360.simulation.services.event_broadcaster import (
    SessionEventBroadcaster,
    SessionEventType,
    create_event,
)


def test_broadcaster_publish_and_history() -> None:
    bus = SessionEventBroadcaster()
    session_id = "session_b1"

    ev1 = create_event(
        session_id=session_id,
        event_type=SessionEventType.ROUND_STARTED,
        payload={"round": 1},
    )
    ev2 = create_event(
        session_id=session_id,
        event_type=SessionEventType.DIRECTIVE_CREATED,
        payload={"directive_id": "d1"},
        target_role_id="role_medical",
    )

    bus.publish(ev1)
    bus.publish(ev2)

    all_events = bus.get_events(session_id)
    assert len(all_events) == 2

    role_events = bus.get_events(session_id, role_id="role_medical")
    assert len(role_events) == 2

    other_role_events = bus.get_events(session_id, role_id="role_fire")
    assert len(other_role_events) == 1
    assert other_role_events[0].event_type is SessionEventType.ROUND_STARTED


def test_broadcaster_since_event_id_filtering() -> None:
    bus = SessionEventBroadcaster()
    session_id = "session_b2"

    ev1 = create_event(session_id, SessionEventType.SESSION_STATUS_CHANGED, {"status": "ACTIVE"})
    ev2 = create_event(session_id, SessionEventType.ROUND_STARTED, {"round": 1})

    bus.publish(ev1)
    bus.publish(ev2)

    new_events = bus.get_events(session_id, since_event_id=ev1.id)
    assert len(new_events) == 1
    assert new_events[0].id == ev2.id
