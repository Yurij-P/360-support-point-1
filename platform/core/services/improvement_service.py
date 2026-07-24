from datetime import date
from uuid import UUID

from platform.core.domain.models import ImprovementAction, ImprovementPlan


class ImprovementService:
    def create_improvement_action(self, title: str, priority: int, deadline: date | None = None) -> ImprovementAction:
        return ImprovementAction(title=title, priority=priority, deadline=deadline)

    def prioritize_actions(self, actions: list[ImprovementAction]) -> list[ImprovementAction]:
        return sorted(actions, key=lambda action: action.priority)

    def update_action_status(self, action: ImprovementAction, status: str) -> ImprovementAction:
        action.status = status
        return action

    def identify_overdue_actions(self, plan: ImprovementPlan, today: date | None = None) -> list[ImprovementAction]:
        current = today or date.today()
        return [action for action in plan.actions if action.deadline and action.deadline < current and action.status != "completed"]
