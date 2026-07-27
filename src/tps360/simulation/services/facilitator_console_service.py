from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from tps360.core.exceptions import EntityNotFound
from tps360.simulation.domain.task_directive import (
    DirectivePriority,
    TaskDirective,
)


@dataclass(frozen=True)
class CrisisLifecycleProjectionVariant:
    """Projected future crisis event trajectory variant for Facilitator 1-round-ahead vision."""

    variant_id: str  # BEST_CASE_CONTAINED, MODERATE_STABLE, ESCALATION_HAZARD, INFRASTRUCTURE_COLLAPSE, WORST_CASE_CASCADE
    variant_name: str
    hazard_level: str  # LOW, MODERATE, HIGH, CRITICAL, CATASTROPHIC
    projected_impact_summary: str
    suggested_inject_title: str
    suggested_inject_description: str
    suggested_directives: tuple[TaskDirective, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FacilitatorConsoleReadModel:
    """Facilitator Master Console read model containing real-time player states and 5 future lifecycle variants."""

    session_id: str
    status: str
    current_round: int
    simulated_hours_passed: float
    connected_participants_count: int
    assigned_roles_count: int
    pending_lego_cards_count: int
    future_projections_5_variants: tuple[CrisisLifecycleProjectionVariant, ...]


class FacilitatorConsoleService:
    """Facilitator (Game Moderator) Control Center Service providing 1-round-ahead future vision with 5 lifecycle variants, proposal review, and round execution triggers."""

    def __init__(self) -> None:
        self._approved_variants: dict[str, CrisisLifecycleProjectionVariant] = {}


    def generate_5_future_lifecycle_variants(
        self, session_id: str, crisis_type: str, current_round: int
    ) -> tuple[CrisisLifecycleProjectionVariant, ...]:
        """Generates 5 distinct projected future crisis lifecycle variants for Facilitator vision 1 round ahead."""

        title_clean = crisis_type.strip()

        v1 = CrisisLifecycleProjectionVariant(
            variant_id="BEST_CASE_CONTAINED",
            variant_name="🟢 Варіант 1: Оптимістичний (Повна локалізація НС)",
            hazard_level="LOW",
            projected_impact_summary="Рятувальні розрахунки швидко локалізують осередок. Загроза поширення на житлові масиви ліквідована.",
            suggested_inject_title=f"Локалізація події: {title_clean}",
            suggested_inject_description="Осередок небезпеки успішно огороджено. Зафіксовано зниження ризиків.",
        )

        v2 = CrisisLifecycleProjectionVariant(
            variant_id="MODERATE_STABLE",
            variant_name="🔵 Варіант 2: Помірний (Контрольована планова ситуація)",
            hazard_level="MODERATE",
            projected_impact_summary="Ситуація контрольована. Триває планова ліквідація наслідків з очікуваними витратами ресурсів.",
            suggested_inject_title=f"Плановий хід ліквідації: {title_clean}",
            suggested_inject_description="Оперативні служби діють за регламентом у межах визначених секторів.",
        )

        v3 = CrisisLifecycleProjectionVariant(
            variant_id="ESCALATION_HAZARD",
            variant_name="🟡 Варіант 3: Ескалація небезпеки (Виникнення супутньої загрози)",
            hazard_level="HIGH",
            projected_impact_summary="Вогонь або пошкодження поширюються на сусідній об'єкт (склади ПММ чи ЛЕП). Потрібні додаткові сили.",
            suggested_inject_title=f"Загроза поширення: {title_clean}",
            suggested_inject_description="Виявлено ризик займання сусідніх резервуарів. Необхідне негайне підкріплення.",
            suggested_directives=(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=session_id,
                    issuer_role_id="facilitator_moderator",
                    assignee_role_id="emerg-dsns",
                    title="Залучення додаткових розрахунків ДСНС",
                    description="Перекинути резервні пожежні автоцистерни до периметра небезпеки.",
                    target_round=current_round + 1,
                    priority=DirectivePriority.CRITICAL,
                    created_at_round=current_round,
                ),
            ),
        )

        v4 = CrisisLifecycleProjectionVariant(
            variant_id="INFRASTRUCTURE_COLLAPSE",
            variant_name="🟠 Варіант 4: Інфраструктурний колапс (Блокування шляхів/знеструмлення)",
            hazard_level="CRITICAL",
            projected_impact_summary="Зруйновано міст або знеструмлено котельню/лікарню. Виникає логістичний затор та ризик замерзання.",
            suggested_inject_title=f"Критична аварія мережі: {title_clean}",
            suggested_inject_description="Транспортний вузол заблоковано. Лікарня перейшла на резервні генератори.",
            suggested_directives=(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=session_id,
                    issuer_role_id="facilitator_moderator",
                    assignee_role_id="communal-utility",
                    title="Термінове підключення резервних генераторів ОМС",
                    description="Забезпечити резервне живлення медичного закладу та насосної станції.",
                    target_round=current_round + 1,
                    priority=DirectivePriority.CRITICAL,
                    created_at_round=current_round,
                ),
            ),
        )

        v5 = CrisisLifecycleProjectionVariant(
            variant_id="WORST_CASE_CASCADE",
            variant_name="🔴 Варіант 5: Каскадна катастрофа (Повторний удар / Хімічний витек)",
            hazard_level="CATASTROPHIC",
            projected_impact_summary="Високий ризик повторного удару (Double-tap) по рятувальниках або витек хімічних речовин з розльотом у 2 км.",
            suggested_inject_title=f"Каскадна катастрофа: {title_clean}",
            suggested_inject_description="Оголошено радіаційну/хімічну небезпеку та загрозу повторного обстрілу.",
            suggested_directives=(
                TaskDirective(
                    id=str(uuid4()),
                    session_id=session_id,
                    issuer_role_id="facilitator_moderator",
                    assignee_role_id="emerg-dsns",
                    title="Відведення сил в укриття (Протокол Double-tap)",
                    description="Негайно евакуювати перших реагувальників у безпековий периметр.",
                    target_round=current_round + 1,
                    priority=DirectivePriority.CRITICAL,
                    created_at_round=current_round,
                ),
            ),
        )

        return (v1, v2, v3, v4, v5)

    def get_facilitator_console(
        self,
        session_id: str,
        current_round: int = 1,
        crisis_type: str = "Ракетно-дроновий обстріл території громади",
        connected_participants: int = 1,
        assigned_roles: int = 1,
        pending_cards_count: int = 0,
    ) -> FacilitatorConsoleReadModel:

        projections = self.generate_5_future_lifecycle_variants(
            session_id=session_id, crisis_type=crisis_type, current_round=current_round
        )

        return FacilitatorConsoleReadModel(
            session_id=session_id,
            status="RUNNING",
            current_round=current_round,
            simulated_hours_passed=float(current_round * 1.5),
            connected_participants_count=connected_participants,
            assigned_roles_count=assigned_roles,
            pending_lego_cards_count=pending_cards_count,
            future_projections_5_variants=projections,
        )

    def approve_ai_proposal(
        self,
        session_id: str,
        variant_id: str,
        custom_title: str | None = None,
        custom_description: str | None = None,
        current_round: int = 1,
    ) -> dict[str, Any]:
        """Approves a chosen future lifecycle variant by Facilitator, optionally editing title or description."""
        projections = self.generate_5_future_lifecycle_variants(
            session_id=session_id, crisis_type="Кризова подія", current_round=current_round
        )

        matched = next((p for p in projections if p.variant_id == variant_id), None)
        if not matched:
            raise EntityNotFound(f"Lifecycle variant '{variant_id}' not found.")

        title = custom_title.strip() if custom_title and custom_title.strip() else matched.suggested_inject_title
        desc = custom_description.strip() if custom_description and custom_description.strip() else matched.suggested_inject_description

        approved_item = {
            "session_id": session_id,
            "variant_id": matched.variant_id,
            "hazard_level": matched.hazard_level,
            "approved_title": title,
            "approved_description": desc,
            "directives_count": len(matched.suggested_directives),
            "status": "APPROVED_BY_FACILITATOR",
        }

        self._approved_variants[session_id] = matched
        return approved_item

    def advance_session_round(
        self, session_id: str, current_round: int, mitigation_score_pct: float = 0.0
    ) -> dict[str, Any]:
        """Advances the session round or completes the simulation dynamically based on AI evaluation of player decisions and resource investments."""
        is_completed = mitigation_score_pct >= 100.0
        if is_completed:
            return {
                "session_id": session_id,
                "current_round": current_round,
                "total_rounds_played": current_round,
                "mitigation_score_pct": mitigation_score_pct,
                "is_session_finished": True,
                "status": "COMPLETED_SUCCESS",
                "message": f"ШІ оцінив результативність залучених ресурсів та рішень гравців: кризову подію повністю ліквідовано за {current_round} ранд(ів). Симуляцію успішно завершено!",
            }

        next_round = current_round + 1
        return {
            "session_id": session_id,
            "previous_round": current_round,
            "new_round": next_round,
            "total_rounds_played": current_round,
            "mitigation_score_pct": mitigation_score_pct,
            "is_session_finished": False,
            "clock_simulated_hours": float(next_round * 1.5),
            "status": "ROUND_ADVANCED",
            "message": f"Рішення та ресурси розраховано ШІ (рівень ліквідації: {mitigation_score_pct:.1f}%). Симуляцію переведено до Раунду {next_round}.",
        }

