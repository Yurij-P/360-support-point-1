from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.task_directive import (
    DirectivePriority,
    TaskDirective,
)
from tps360.simulation.domain.time_dilation import (
    SimulationRoundClock,
)


@dataclass(frozen=True)
class CopilotInputContext:
    """Immutable input context provided to AI Crisis Copilot for generating round dynamic events."""

    session_id: str
    current_round: int
    crisis_type: str
    clock: SimulationRoundClock
    submitted_directives: tuple[TaskDirective, ...] = ()
    resource_levels: dict[str, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id or not self.crisis_type:
            raise DomainRuleViolation("Copilot input context requires session_id and crisis_type.")
        if self.current_round < 0:
            raise DomainRuleViolation("Current round cannot be negative.")


@dataclass(frozen=True)
class CopilotGenerationResult:
    """Immutable AI Copilot proposal for facilitator review before SSE publication."""

    session_id: str
    round_number: int
    simulated_hours_passed: float
    narrative_summary: str
    suggested_inject_title: str
    suggested_inject_description: str
    suggested_directives: tuple[TaskDirective, ...]
    status: str = "PROPOSED_BY_AI"


class AICrisisCopilotService:
    """Human-in-the-Loop AI Crisis Copilot generating dynamic round injects and role directive proposals."""

    @staticmethod
    def generate_round_proposal(context: CopilotInputContext) -> CopilotGenerationResult:
        simulated_hours = context.clock.total_simulated_hours_per_round
        velocity = context.clock.velocity
        normalized_crisis = context.crisis_type.strip().upper()

        # Build dynamic narrative grounded in crisis type and time dilation
        narrative_parts: list[str] = []
        suggested_title = ""
        suggested_desc = ""
        proposed_directives: list[TaskDirective] = []

        if normalized_crisis in ("FIRE", "MILITARY_ATTACK", "FLASH_FLOOD"):
            suggested_title = f"Динамічний розвиток події: {normalized_crisis} (Раунд {context.current_round})"
            narrative_parts.append(
                f"За {simulated_hours:.1f} год симуляційного часу (швидкий перебіг 1:30) зафіксовано нові осередки виклику."
            )
            suggested_desc = (
                f"За останні {simulated_hours:.1f} год зафіксовано додаткові пошкодження інфраструктури. "
                f"Потрібна оперативна передислокація підрозділів."
            )
            proposed_directives.append(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=context.session_id,
                    issuer_role_id="facilitator",
                    assignee_role_id="head_of_emergency",
                    title="Оперативна передислокація сил",
                    description="Забезпечити огородження та захист критичних об'єктів у небезпечному секторі.",
                    target_round=context.current_round + 1,
                    priority=DirectivePriority.CRITICAL,
                    created_at_round=context.current_round,
                )
            )

        elif normalized_crisis in ("CHOLERA", "WATER_CONTAMINATION", "CHEMICAL_SPILL"):
            suggested_title = f"Епідеміологічна оцінка: {normalized_crisis} (Раунд {context.current_round})"
            narrative_parts.append(
                f"За {simulated_hours:.1f} год симуляційного часу (середня динаміка 1:60) зафіксовано динаміку поширення інфекції питної води."
            )
            suggested_desc = (
                f"Аналіз проб за {simulated_hours:.1f} год підтверджує ризик поширення збудників у центральному водогоні. "
                f"Необхідне термінове введення санітарних обмежень."
            )
            proposed_directives.append(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=context.session_id,
                    issuer_role_id="facilitator",
                    assignee_role_id="chief_medical_officer",
                    title="Санітарно-епідеміологічний блокпост та моніторинг",
                    description="Організувати лабораторні проби питної води та розгорнути ізолятор первинного огляду.",
                    target_round=context.current_round + 1,
                    priority=DirectivePriority.HIGH,
                    created_at_round=context.current_round,
                )
            )

        elif normalized_crisis in ("LIVESTOCK_MORTALITY", "QUARANTINE_ISOLATION", "BLACKOUT"):
            suggested_title = f"Епізоотична та санітарна обстановка: {normalized_crisis} (Раунд {context.current_round})"
            narrative_parts.append(
                f"За {simulated_hours:.1f} год симуляційного часу (максимальний макро-перебіг 1:90) зафіксовано потребу у тривалій санітарній ізоляції."
            )
            suggested_desc = (
                f"За останні {simulated_hours:.1f} год симуляційного періоду виявлено осередки падіжу худоби та потребу карантинного обмеження території. "
                f"Потрібна санітарна утилізація та контроль кордонів громади."
            )
            proposed_directives.append(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=context.session_id,
                    issuer_role_id="facilitator",
                    assignee_role_id="chief_veterinary_inspector",
                    title="Встановлення карантинної зони та санітарний кордон",
                    description="Організувати протиепізоотичні заходи, утилізацію та обмеження ввезення/вивезення продукції.",
                    target_round=context.current_round + 1,
                    priority=DirectivePriority.CRITICAL,
                    created_at_round=context.current_round,
                )
            )

        else:
            suggested_title = f"Ситуаційний звіт кризової події (Раунд {context.current_round})"
            suggested_desc = f"Оновлення обстановки за {simulated_hours:.1f} год симуляції."

        # Incorporate participant submitted reports into AI narrative summary
        if context.submitted_directives:
            reports_summary = "; ".join(
                f"[{d.assignee_role_id}]: {d.completion_report}"
                for d in context.submitted_directives
                if d.completion_report
            )
            if reports_summary:
                narrative_parts.append(f"Враховано звіти ролей: {reports_summary}")

        full_narrative = " ".join(narrative_parts) if narrative_parts else suggested_desc

        return CopilotGenerationResult(
            session_id=context.session_id,
            round_number=context.current_round,
            simulated_hours_passed=simulated_hours,
            narrative_summary=full_narrative,
            suggested_inject_title=suggested_title,
            suggested_inject_description=suggested_desc,
            suggested_directives=tuple(proposed_directives),
        )
