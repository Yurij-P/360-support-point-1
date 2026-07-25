from uuid import UUID

from tps360.core.exceptions import NotFoundError
from tps360.simulation.domain.session import FacilitatedSession


class SessionRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, FacilitatedSession] = {}

    def add(self, session: FacilitatedSession) -> FacilitatedSession:
        self.items[session.id] = session
        return session

    def get(self, session_id: UUID) -> FacilitatedSession:
        if session_id not in self.items:
            raise NotFoundError("Session not found")
        return self.items[session_id]
