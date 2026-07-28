from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from .community_id import CommunityId
from .enums import CapabilityDomain, HazardCategory, LifecycleStatus, MaturityLevel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)


class Organization(Entity):
    name: str
    type: str = "community"


class Person(Entity):
    full_name: str
    organization_id: UUID | None = None


class Role(Entity):
    name: str
    description: str | None = None


class Resource(Entity):
    name: str
    type: str
    quantity: float = Field(ge=0)
    unit: str
    availability_status: str
    owner: str
    location: str | None = None
    activation_time_minutes: int = Field(ge=0)
    limitations: list[str] = Field(default_factory=list)


class Community(Entity):
    # Community identity migrates to a KATOTTG string (ADR-0016); keep an
    # auto str default so existing constructions without an id still work.
    id: CommunityId = Field(default_factory=lambda: str(uuid4()))  # type: ignore[assignment]
    name: str
    code: str = Field(min_length=1)
    oblast: str
    raion: str | None = None
    settlements: list[str] = Field(default_factory=list)
    population: int = Field(ge=0)
    area_km2: float = Field(ge=0)
    organizations: list[Organization] = Field(default_factory=list)
    critical_infrastructure: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Hazard(Entity):
    name: str
    category: HazardCategory
    description: str
    probability: float = Field(ge=0, le=100)
    potential_impact: float = Field(ge=0, le=100)
    geographic_scope: str


class Vulnerability(Entity):
    name: str
    category: str
    affected_groups: list[str] = Field(default_factory=list)
    affected_assets: list[str] = Field(default_factory=list)
    severity: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)


class Capability(Entity):
    name: str
    domain: CapabilityDomain
    description: str
    current_level: float = Field(ge=0, le=100)
    target_level: float = Field(ge=0, le=100)
    responsible_organization: str
    resources: list[Resource] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class Risk(Entity):
    community_id: CommunityId
    hazard: Hazard
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    probability_score: float = Field(ge=0, le=100)
    impact_score: float = Field(ge=0, le=100)
    exposure_score: float = Field(ge=0, le=100)
    capability_modifier: float = Field(ge=0, le=100)
    overall_score: float | None = Field(default=None, ge=0, le=100)
    confidence_level: str
    evidence: list[str] = Field(default_factory=list)


class PreparednessAssessment(Entity):
    community_id: CommunityId
    assessment_date: date
    dimensions: dict[str, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    assessor: str
    status: LifecycleStatus = LifecycleStatus.DRAFT
    confidence_level: str
    total_score: float | None = Field(default=None, ge=0, le=100)
    maturity_level: MaturityLevel | None = None


class Inject(Entity):
    scenario_id: UUID
    sequence: int = Field(ge=1)
    scheduled_offset_minutes: int = Field(ge=0)
    title: str
    description: str
    delivery_channel: str
    target_roles: list[str] = Field(default_factory=list)
    expected_actions: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    delivered_at: datetime | None = None


class Scenario(Entity):
    title: str
    description: str
    hazards: list[Hazard] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    participants: list[str] = Field(default_factory=list)
    initial_conditions: list[str] = Field(default_factory=list)
    injects: list[Inject] = Field(default_factory=list)
    expected_capabilities: list[CapabilityDomain] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    duration_minutes: int = Field(gt=0)
    status: LifecycleStatus = LifecycleStatus.DRAFT
    version: str = "0.1"


class Decision(Entity):
    simulation_id: UUID
    actor: str
    timestamp: datetime = Field(default_factory=utcnow)
    description: str
    rationale: str
    selected_action: str
    alternatives: list[str] = Field(default_factory=list)
    expected_effect: str | None = None
    actual_effect: str | None = None


class Observation(Entity):
    simulation_id: UUID
    observer: str
    timestamp: datetime = Field(default_factory=utcnow)
    category: str
    description: str
    related_capability: CapabilityDomain | None = None
    severity: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)


class Evaluation(Entity):
    simulation_id: UUID
    criteria_results: dict[str, float] = Field(default_factory=dict)
    capability_scores: dict[str, float] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    lessons_identified: list[str] = Field(default_factory=list)
    overall_score: float | None = Field(default=None, ge=0, le=100)
    confidence_level: str


class ImprovementAction(BaseModel):
    title: str
    priority: int = Field(ge=1, le=5)
    status: str = "open"
    deadline: date | None = None


class ImprovementPlan(Entity):
    community_id: CommunityId
    source_assessment_id: UUID | None = None
    source_simulation_id: UUID | None = None
    actions: list[ImprovementAction] = Field(default_factory=list)
    responsible_parties: list[str] = Field(default_factory=list)
    deadlines: list[date] = Field(default_factory=list)
    indicators: list[str] = Field(default_factory=list)
    status: LifecycleStatus = LifecycleStatus.DRAFT
    review_date: date | None = None

    @model_validator(mode="after")
    def has_source(self) -> "ImprovementPlan":
        if self.source_assessment_id is None and self.source_simulation_id is None:
            raise ValueError("Improvement plan requires an assessment or simulation source")
        return self


class Simulation(Entity):
    scenario_id: UUID
    community_id: CommunityId
    status: LifecycleStatus = LifecycleStatus.DRAFT
    started_at: datetime | None = None
    completed_at: datetime | None = None
    participants: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    evaluation: Evaluation | None = None
    after_action_review: list[str] = Field(default_factory=list)
