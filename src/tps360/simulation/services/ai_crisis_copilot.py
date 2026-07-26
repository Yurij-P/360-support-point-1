from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4

from tps360.core.exceptions import DomainRuleViolation
from tps360.geospatial.value_objects import BoundingBox
from tps360.simulation.domain.task_directive import (
    DirectivePriority,
    TaskDirective,
)
from tps360.simulation.domain.time_dilation import (
    CrisisVelocity,
    SimulationRoundClock,
)


@dataclass(frozen=True)
class CopilotInputContext:
    """Immutable input context for AI Crisis Copilot supporting OpenStreetMap community spatial boundaries, OSINT feeds, and open crisis types."""

    session_id: str
    current_round: int
    crisis_type: str  # Open dynamic crisis description (e.g. "Аварія колектора", "Спалах холери", "Падіж худоби", "Дезінформація")
    clock: SimulationRoundClock
    community_boundary_bbox: BoundingBox | None = None  # OpenStreetMap administrative boundary box
    osm_relation_id: str | None = None  # OpenStreetMap relation ID for community polygon boundary
    official_sources_feed: tuple[str, ...] = ()  # External OSINT & Official reports (DSNS, MOH, Media)
    submitted_directives: tuple[TaskDirective, ...] = ()
    resource_levels: dict[str, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id or not self.crisis_type:
            raise DomainRuleViolation("Copilot input context requires session_id and crisis_type.")
        if self.current_round < 0:
            raise DomainRuleViolation("Current round cannot be negative.")


@dataclass(frozen=True)
class CopilotGenerationResult:
    """Immutable AI Copilot proposal for Game Moderator review before SSE publication to players."""

    session_id: str
    round_number: int
    simulated_hours_passed: float
    narrative_summary: str
    suggested_inject_title: str
    suggested_inject_description: str
    suggested_directives: tuple[TaskDirective, ...]
    is_spatial_bounded_by_osm: bool = True
    status: str = "PROPOSED_BY_AI"


class AICrisisCopilotService:
    """Autonomous AI Crisis Engine providing objective crisis lifecycle modeling bounded by OpenStreetMap community spatial limits under System Admin governance & Facilitator (Game Moderator) session moderation."""

    @staticmethod
    def generate_round_proposal(context: CopilotInputContext) -> CopilotGenerationResult:
        simulated_hours = context.clock.total_simulated_hours_per_round
        velocity = context.clock.velocity
        crisis_title_text = context.crisis_type.strip()

        spatial_note = (
            f" [Межі: OpenStreetMap BoundingBox min_lat={context.community_boundary_bbox.min_lat:.3f}, max_lat={context.community_boundary_bbox.max_lat:.3f}]"
            if context.community_boundary_bbox
            else " [Обмежено картографічними межами OpenStreetMap громади]"
        )

        narrative_parts: list[str] = [
            f"Динамічний розвиток кризової події «{crisis_title_text}» у межах громади{spatial_note} за {simulated_hours:.1f} год симуляційного часу (динаміка {velocity})."
        ]

        # Integrate official OSINT & Media feeds into the AI crisis model narrative
        if context.official_sources_feed:
            feed_text = " | ".join(context.official_sources_feed)
            narrative_parts.append(f"Аналітика джерел та ЗМІ: {feed_text}.")

        suggested_title = f"Ситуаційне оновлення: {crisis_title_text} (Раунд {context.current_round})"
        suggested_desc = f"За останні {simulated_hours:.1f} год симуляції у межах OpenStreetMap території громади виявлено зміни."

        proposed_directives: list[TaskDirective] = []

        # Dynamic role assignment recommendation based on crisis velocity
        if velocity is CrisisVelocity.FAST:
            proposed_directives.append(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=context.session_id,
                    issuer_role_id="facilitator_moderator",
                    assignee_role_id="head_of_emergency",
                    title="Оперативне огородження та реакція у межах громади",
                    description=f"Вжити невідкладних заходів реагування у зоні OpenStreetMap події «{crisis_title_text}».",
                    target_round=context.current_round + 1,
                    priority=DirectivePriority.CRITICAL,
                    created_at_round=context.current_round,
                )
            )
        elif velocity is CrisisVelocity.SLOW_MAX:
            proposed_directives.append(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=context.session_id,
                    issuer_role_id="facilitator_moderator",
                    assignee_role_id="chief_sanitary_inspector",
                    title="Карантинна ізоляція периметра OpenStreetMap громади",
                    description=f"Встановити санітарні блокпости по кордону openstreetmap.org громади для осередку «{crisis_title_text}».",
                    target_round=context.current_round + 1,
                    priority=DirectivePriority.HIGH,
                    created_at_round=context.current_round,
                )
            )
        else:
            proposed_directives.append(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=context.session_id,
                    issuer_role_id="facilitator_moderator",
                    assignee_role_id="chief_medical_officer",
                    title="Лабораторний моніторинг території громади",
                    description=f"Забезпечити моніторинг у геопросторових межах OpenStreetMap громади під час загрози «{crisis_title_text}».",
                    target_round=context.current_round + 1,
                    priority=DirectivePriority.HIGH,
                    created_at_round=context.current_round,
                )
            )

        # Incorporate participant submitted reports into AI narrative summary
        if context.submitted_directives:
            reports_summary = "; ".join(
                f"[{d.assignee_role_id}]: {d.completion_report}"
                for d in context.submitted_directives
                if d.completion_report
            )
            if reports_summary:
                narrative_parts.append(f"Враховано звіти ролей: {reports_summary}")

        full_narrative = " ".join(narrative_parts)

        return CopilotGenerationResult(
            session_id=context.session_id,
            round_number=context.current_round,
            simulated_hours_passed=simulated_hours,
            narrative_summary=full_narrative,
            suggested_inject_title=suggested_title,
            suggested_inject_description=suggested_desc,
            suggested_directives=tuple(proposed_directives),
            is_spatial_bounded_by_osm=True,
        )
