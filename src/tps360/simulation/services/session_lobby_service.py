from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from tps360.core.exceptions import DomainRuleViolation, EntityNotFound

# Room Capacity Bounds
# Demo / Integration Testing Mode: Min 1, Max 50
# Production Target: Min 5, Max 20 participants
DEMO_MIN_CAPACITY = 1
DEMO_MAX_CAPACITY = 50
PROD_MIN_CAPACITY = 5
PROD_MAX_CAPACITY = 20


@dataclass(frozen=True)
class LobbyParticipantStatus:
    participant_id: str
    display_name: str
    token: str
    role_id: str | None = None
    joined_at_round: int = 0

    @property
    def is_assigned(self) -> bool:
        return self.role_id is not None and len(self.role_id.strip()) > 0


@dataclass(frozen=True)
class LobbyRoomStatus:
    session_id: str
    capacity: int
    connected_count: int
    assigned_count: int
    participants: tuple[LobbyParticipantStatus, ...]
    can_start: bool
    readiness_message: str


class SessionLobbyService:
    """Manages pre-session multi-participant standby room, token registration, role assignment, and start readiness guards.
    
    Capacity configuration:
    - Demo Testing Mode: Allows 1 to 50 participants for rapid single-developer or load testing.
    - Production Target: Designed for 5 to 20 operational role participants per crisis simulation session.
    """

    def __init__(self, enforce_prod_capacity: bool = False) -> None:
        self._rooms: dict[str, dict[str, Any]] = {}
        self._enforce_prod_capacity = enforce_prod_capacity

    def create_room(self, session_id: str, capacity: int = 10) -> LobbyRoomStatus:
        min_cap = PROD_MIN_CAPACITY if self._enforce_prod_capacity else DEMO_MIN_CAPACITY
        max_cap = PROD_MAX_CAPACITY if self._enforce_prod_capacity else DEMO_MAX_CAPACITY

        if capacity < min_cap or capacity > max_cap:
            raise DomainRuleViolation(
                f"Lobby room capacity must be between {min_cap} and {max_cap} participants."
            )
        if session_id in self._rooms:
            raise DomainRuleViolation(f"Lobby room for session '{session_id}' already exists.")

        self._rooms[session_id] = {
            "session_id": session_id,
            "capacity": capacity,
            "participants": [],
        }
        return self.get_lobby_status(session_id)

    def join_standby_room(self, session_id: str, display_name: str) -> LobbyParticipantStatus:
        if not display_name or not display_name.strip():
            raise DomainRuleViolation("Participant display name cannot be empty.")

        if session_id not in self._rooms:
            # Auto-create room if not present for ease of testing
            self.create_room(session_id=session_id, capacity=10)

        room = self._rooms[session_id]
        participants: list[LobbyParticipantStatus] = room["participants"]  # type: ignore

        if len(participants) >= int(room["capacity"]):  # type: ignore
            raise DomainRuleViolation(f"Lobby room for session '{session_id}' has reached maximum capacity ({room['capacity']}).")

        participant = LobbyParticipantStatus(
            participant_id=f"part_{uuid4().hex[:8]}",
            display_name=display_name.strip(),
            token=f"part_token_{uuid4().hex[:12]}",
            role_id=None,
        )
        participants.append(participant)
        return participant

    def assign_participant_role(self, session_id: str, participant_id: str, role_id: str) -> LobbyParticipantStatus:
        if not role_id or not role_id.strip():
            raise DomainRuleViolation("Role ID cannot be empty.")

        if session_id not in self._rooms:
            raise EntityNotFound(f"Lobby room for session '{session_id}' not found.")

        room = self._rooms[session_id]
        participants: list[LobbyParticipantStatus] = room["participants"]  # type: ignore

        target_index = -1
        for idx, p in enumerate(participants):
            if p.participant_id == participant_id:
                target_index = idx
                break

        if target_index == -1:
            raise EntityNotFound(f"Participant '{participant_id}' not found in session '{session_id}' lobby.")

        # Check if role is already assigned to another participant in this session
        for p in participants:
            if p.role_id == role_id.strip() and p.participant_id != participant_id:
                raise DomainRuleViolation(f"Role '{role_id}' is already assigned to participant '{p.display_name}'.")

        old = participants[target_index]
        updated = LobbyParticipantStatus(
            participant_id=old.participant_id,
            display_name=old.display_name,
            token=old.token,
            role_id=role_id.strip(),
            joined_at_round=old.joined_at_round,
        )
        participants[target_index] = updated
        return updated

    def get_lobby_status(self, session_id: str) -> LobbyRoomStatus:
        if session_id not in self._rooms:
            raise EntityNotFound(f"Lobby room for session '{session_id}' not found.")

        room = self._rooms[session_id]
        participants: list[LobbyParticipantStatus] = room["participants"]  # type: ignore
        capacity = int(room["capacity"])  # type: ignore

        assigned_count = sum(1 for p in participants if p.is_assigned)
        connected_count = len(participants)

        # Pre-start Guard Rules:
        # 1. At least 1 participant connected (or PROD_MIN_CAPACITY in production mode)
        # 2. All connected participants MUST have an assigned role
        min_required = PROD_MIN_CAPACITY if self._enforce_prod_capacity else 1

        if connected_count < min_required:
            can_start = False
            message = f"Кімната очікування має {connected_count} підключених гравців (мінімум за регламентом: {min_required}). Очікуйте підключення."
        elif assigned_count < connected_count:
            unassigned_names = [p.display_name for p in participants if not p.is_assigned]
            can_start = False
            message = f"Запуск заблоковано: наступні гравці залишаються без ролі: {', '.join(unassigned_names)}."
        else:
            can_start = True
            message = f"Усі підключені гравці ({assigned_count}/{connected_count}) отримали оперативні ролі. Сесія готова до старту."

        return LobbyRoomStatus(
            session_id=session_id,
            capacity=capacity,
            connected_count=connected_count,
            assigned_count=assigned_count,
            participants=tuple(participants),
            can_start=can_start,
            readiness_message=message,
        )

    def validate_session_start_readiness(self, session_id: str) -> bool:
        status = self.get_lobby_status(session_id)
        if not status.can_start:
            raise DomainRuleViolation(status.readiness_message)
        return True
