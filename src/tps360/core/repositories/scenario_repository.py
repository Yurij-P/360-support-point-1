from uuid import UUID
from tps360.core.domain.models import Scenario
from tps360.core.exceptions import NotFoundError
class ScenarioRepository:
    def __init__(self) -> None: self.items: dict[UUID, Scenario] = {}
    def add(self, item: Scenario) -> Scenario: self.items[item.id] = item; return item
    def get(self, item_id: UUID) -> Scenario:
        if item_id not in self.items: raise NotFoundError("Scenario not found")
        return self.items[item_id]
