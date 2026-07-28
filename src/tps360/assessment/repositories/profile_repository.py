from uuid import UUID

from tps360.assessment.domain.profile import CommunityPreparednessProfile
from tps360.core.domain.community_id import CommunityId
from tps360.core.exceptions import NotFoundError


class PreparednessProfileRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, CommunityPreparednessProfile] = {}

    def add(self, p: CommunityPreparednessProfile) -> CommunityPreparednessProfile:
        if p.id in self.items:
            raise ValueError("Duplicate profile")
        self.items[p.id] = p
        return p

    def get(self, profile_id: UUID) -> CommunityPreparednessProfile:
        if profile_id not in self.items:
            raise NotFoundError("Profile not found")
        return self.items[profile_id]

    def get_by_community(self, community_id: CommunityId) -> CommunityPreparednessProfile | None:
        return next((p for p in self.items.values() if p.community_id == community_id), None)

    def save(self, p: CommunityPreparednessProfile) -> CommunityPreparednessProfile:
        self.items[p.id] = p
        return p
