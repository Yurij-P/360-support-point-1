from uuid import UUID
from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation, NotFoundError

class CommunityRepository:
    def __init__(self) -> None: self.items: dict[UUID, Community] = {}
    def add(self, item: Community) -> Community:
        if any(existing.code == item.code for existing in self.items.values()): raise DomainRuleViolation("Community code must be unique")
        self.items[item.id] = item; return item
    def get(self, item_id: UUID) -> Community:
        if item_id not in self.items: raise NotFoundError("Community not found")
        return self.items[item_id]
