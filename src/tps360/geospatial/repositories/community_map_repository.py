from uuid import UUID

from ..domain.enums import MapStatus
from ..domain.models import CommunityMap


class CommunityMapRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, CommunityMap] = {}

    def add(self, m: CommunityMap) -> CommunityMap:
        if m.id in self.items:
            raise ValueError("Duplicate map")
        self.items[m.id] = m
        return m

    def get(self, i: UUID) -> CommunityMap:
        return self.items[i]

    def list_by_community(self, c: UUID) -> list[CommunityMap]:
        return [m for m in self.items.values() if m.community_id == c]

    def save(self, m: CommunityMap) -> CommunityMap:
        if m.status is MapStatus.ACTIVE:
            for o in self.list_by_community(m.community_id):
                if o.id != m.id and o.status is MapStatus.ACTIVE:
                    o.status = MapStatus.ARCHIVED
        self.items[m.id] = m
        return m

    def get_active_by_community(self, c: UUID) -> CommunityMap | None:
        return next((m for m in self.list_by_community(c) if m.status is MapStatus.ACTIVE), None)
