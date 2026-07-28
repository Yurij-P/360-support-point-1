from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from tps360.core.domain.community_id import CommunityId
from tps360.core.domain.models import Entity


class CommunityPreparednessProfile(Entity):
    community_id: CommunityId
    assessment_id: UUID | None = None
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    risks: list[dict[str, Any]] = Field(default_factory=list)
    improvement_priorities: list[str] = Field(default_factory=list)
    confidence_level: str = "LOW"
    version: str = "0.1"
    is_public: bool = False
    agreed_by_community: bool = False
    agreed_at: datetime | None = None
