from uuid import UUID
from platform.core.domain.models import PreparednessAssessment
from platform.core.exceptions import NotFoundError
class AssessmentRepository:
    def __init__(self) -> None: self.items: dict[UUID, PreparednessAssessment] = {}
    def add(self, item: PreparednessAssessment) -> PreparednessAssessment: self.items[item.id] = item; return item
    def get(self, item_id: UUID) -> PreparednessAssessment:
        if item_id not in self.items: raise NotFoundError("Assessment not found")
        return self.items[item_id]
