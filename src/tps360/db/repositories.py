from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from tps360.core.domain.community_id import CommunityId
from tps360.core.domain.models import Community, PreparednessAssessment, Simulation
from tps360.core.exceptions import DomainRuleViolation, NotFoundError
from tps360.db.orm_models import (
    AssessmentRow,
    CommunityRow,
    DirectiveRow,
    SessionRow,
    SimulationRow,
)
from tps360.simulation.domain.session import FacilitatedSession
from tps360.simulation.domain.task_directive import (
    DirectivePriority,
    DirectiveStatus,
    TaskDirective,
)


def _community_to_row(item: Community) -> CommunityRow:
    return CommunityRow(
        id=str(item.id),
        code=item.code,
        name=item.name,
        oblast=item.oblast,
        data=item.model_dump(mode="json"),
    )


def _community_from_row(row: CommunityRow) -> Community:
    return Community.model_validate(row.data)


def _simulation_to_row(item: Simulation) -> SimulationRow:
    return SimulationRow(
        id=str(item.id),
        community_id=str(item.community_id),
        data=item.model_dump(mode="json"),
    )


def _simulation_from_row(row: SimulationRow) -> Simulation:
    return Simulation.model_validate(row.data)


def _assessment_to_row(item: PreparednessAssessment) -> AssessmentRow:
    return AssessmentRow(
        id=str(item.id),
        community_id=str(item.community_id),
        data=item.model_dump(mode="json"),
    )


def _assessment_from_row(row: AssessmentRow) -> PreparednessAssessment:
    return PreparednessAssessment.model_validate(row.data)


def _session_to_dict(session: FacilitatedSession) -> dict[str, Any]:
    data = session.model_dump(mode="json", exclude={"participants"})
    data["facilitator_token_digest"] = session.facilitator_token_digest
    data["join_token_digest"] = session.join_token_digest
    data["participants"] = [
        {**participant.model_dump(mode="json"), "participant_token_digest": participant.participant_token_digest}
        for participant in session.participants
    ]
    return data


def _session_from_dict(data: dict[str, Any]) -> FacilitatedSession:
    return FacilitatedSession.model_validate(data)


def _directive_to_dict(directive: TaskDirective) -> dict[str, Any]:
    return {
        "id": directive.id,
        "session_id": directive.session_id,
        "issuer_role_id": directive.issuer_role_id,
        "assignee_role_id": directive.assignee_role_id,
        "title": directive.title,
        "description": directive.description,
        "target_round": directive.target_round,
        "task_execution_id": directive.task_execution_id,
        "status": directive.status.value,
        "priority": directive.priority.value,
        "completion_report": directive.completion_report,
        "created_at_round": directive.created_at_round,
        "completed_at_round": directive.completed_at_round,
    }


def _directive_from_row(row: DirectiveRow) -> TaskDirective:
    data = row.data
    return TaskDirective(
        id=data["id"],
        session_id=data["session_id"],
        issuer_role_id=data["issuer_role_id"],
        assignee_role_id=data["assignee_role_id"],
        title=data["title"],
        description=data["description"],
        target_round=data["target_round"],
        task_execution_id=data.get("task_execution_id"),
        status=DirectiveStatus(data["status"]),
        priority=DirectivePriority(data["priority"]),
        completion_report=data.get("completion_report"),
        created_at_round=data.get("created_at_round", 0),
        completed_at_round=data.get("completed_at_round"),
    )


class SQLCommunityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, item: Community) -> Community:
        existing = self.db.execute(
            select(CommunityRow).where(CommunityRow.code == item.code)
        ).scalar_one_or_none()
        if existing is not None:
            raise DomainRuleViolation("Community code must be unique")
        self.db.add(_community_to_row(item))
        self.db.flush()
        return item

    def get(self, item_id: CommunityId) -> Community:
        row = self.db.get(CommunityRow, str(item_id))
        if row is None:
            raise NotFoundError("Community not found")
        return _community_from_row(row)

    def list_all(self) -> list[Community]:
        rows = self.db.execute(select(CommunityRow)).scalars().all()
        return [_community_from_row(row) for row in rows]


class SQLSimulationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, item: Simulation) -> Simulation:
        self.db.add(_simulation_to_row(item))
        self.db.flush()
        return item

    def get(self, item_id: UUID) -> Simulation:
        row = self.db.get(SimulationRow, str(item_id))
        if row is None:
            raise NotFoundError("Simulation not found")
        return _simulation_from_row(row)

    def save(self, item: Simulation) -> Simulation:
        row = self.db.get(SimulationRow, str(item.id))
        if row is None:
            self.db.add(_simulation_to_row(item))
        else:
            row.community_id = str(item.community_id)
            row.data = item.model_dump(mode="json")
        self.db.flush()
        return item


class SQLAssessmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, item: PreparednessAssessment) -> PreparednessAssessment:
        self.db.add(_assessment_to_row(item))
        self.db.flush()
        return item

    def get(self, item_id: UUID) -> PreparednessAssessment:
        row = self.db.get(AssessmentRow, str(item_id))
        if row is None:
            raise NotFoundError("Assessment not found")
        return _assessment_from_row(row)

    def list_all(self) -> list[PreparednessAssessment]:
        rows = self.db.execute(select(AssessmentRow)).scalars().all()
        return [_assessment_from_row(row) for row in rows]


class SQLSessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, session: FacilitatedSession) -> FacilitatedSession:
        self.db.add(
            SessionRow(
                id=str(session.id),
                community_id=str(session.community_id),
                status=session.status.value,
                created_at=datetime.now(timezone.utc),
                data=_session_to_dict(session),
            )
        )
        self.db.flush()
        return session

    def get(self, session_id: UUID) -> FacilitatedSession:
        row = self.db.get(SessionRow, str(session_id))
        if row is None:
            raise NotFoundError("Session not found")
        return _session_from_dict(row.data)

    def save(self, session: FacilitatedSession) -> FacilitatedSession:
        row = self.db.get(SessionRow, str(session.id))
        if row is None:
            row = SessionRow(
                id=str(session.id),
                community_id=str(session.community_id),
                status=session.status.value,
                created_at=datetime.now(timezone.utc),
                data=_session_to_dict(session),
            )
            self.db.add(row)
        else:
            row.community_id = str(session.community_id)
            row.status = session.status.value
            row.data = _session_to_dict(session)
        self.db.flush()
        return session


class SQLDirectiveRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, directive: TaskDirective) -> TaskDirective:
        self.db.add(
            DirectiveRow(
                id=directive.id,
                session_id=directive.session_id,
                issuer_role_id=directive.issuer_role_id,
                assignee_role_id=directive.assignee_role_id,
                status=directive.status.value,
                priority=directive.priority.value,
                data=_directive_to_dict(directive),
            )
        )
        self.db.flush()
        return directive

    def get(self, directive_id: str) -> TaskDirective:
        row = self.db.get(DirectiveRow, directive_id)
        if row is None:
            raise NotFoundError("Directive not found.")
        return _directive_from_row(row)

    def save(self, directive: TaskDirective) -> TaskDirective:
        row = self.db.get(DirectiveRow, directive.id)
        if row is None:
            row = DirectiveRow(
                id=directive.id,
                session_id=directive.session_id,
                issuer_role_id=directive.issuer_role_id,
                assignee_role_id=directive.assignee_role_id,
                status=directive.status.value,
                priority=directive.priority.value,
                data=_directive_to_dict(directive),
            )
            self.db.add(row)
        else:
            row.session_id = directive.session_id
            row.issuer_role_id = directive.issuer_role_id
            row.assignee_role_id = directive.assignee_role_id
            row.status = directive.status.value
            row.priority = directive.priority.value
            row.data = _directive_to_dict(directive)
        self.db.flush()
        return directive

    def list_by_session(self, session_id: str) -> list[TaskDirective]:
        rows = self.db.execute(
            select(DirectiveRow).where(DirectiveRow.session_id == session_id)
        ).scalars().all()
        return [_directive_from_row(row) for row in rows]
