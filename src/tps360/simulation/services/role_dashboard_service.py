from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import uuid4

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.task_directive import TaskDirective

# Default Initial Resource Balances per Role Type
ROLE_INITIAL_RESOURCES: dict[str, dict[str, Decimal]] = {
    "head_of_emergency": {
        "fire_trucks": Decimal("10"),
        "rescue_personnel": Decimal("40"),
        "fuel_liters": Decimal("5000"),
        "heavy_equipment": Decimal("5"),
    },
    "chief_medical_officer": {
        "ambulances": Decimal("8"),
        "medical_personnel": Decimal("30"),
        "medical_kits": Decimal("500"),
        "generators": Decimal("4"),
        "backup_generators": Decimal("4"),
        "fuel_liters": Decimal("2000"),
    },
    "chief_sanitary_inspector": {
        "decontamination_units": Decimal("3"),
        "sanitary_inspectors": Decimal("15"),
        "disinfectant_liters": Decimal("1000"),
        "water_testing_kits": Decimal("100"),
    },
    "chief_police_officer": {
        "patrol_cars": Decimal("12"),
        "police_officers": Decimal("50"),
        "fuel_liters": Decimal("3000"),
        "barricades": Decimal("40"),
    },
    "chief_utility_officer": {
        "utility_repair_trucks": Decimal("6"),
        "utility_workers": Decimal("25"),
        "backup_generators": Decimal("10"),
        "fuel_liters": Decimal("4000"),
    },
}


@dataclass(frozen=True)
class PsychologicalFrictionInject:
    """Psychological stress factor or operational friction event injected into the player's role dashboard."""

    inject_id: str
    session_id: str
    target_role_id: str  # Specific role or "all_roles"
    friction_type: str  # AIR_RAID_SIREN, URGENT_PHONE_CALL, SOCIAL_MEDIA_TROLLING, PUBLIC_PROTEST, STAFF_INCIDENT, FACILITATOR_CUSTOM_FRICTION
    title: str
    description: str
    stress_level_delta: float = 15.0
    audio_siren_signal: bool = False
    created_at_round: int = 1


@dataclass(frozen=True)
class LegoDecisionCard:
    """Modular player-constructed decision card assembled independently from atomic primitives."""

    card_id: str
    session_id: str
    role_id: str
    action_type: str  # e.g. EVACUATE, CONTAIN, EXTINGUISH_FIRE, REPAIR_LINE, DECONTAMINATE, ISOLATE_QUARANTINE, DEPLOY_SHELTER, DISTRIBUTE_SUPPLIES
    target_facility_id: str
    allocated_resources: dict[str, Decimal] = field(default_factory=dict)
    allocated_personnel: int = 0
    custom_instructions: str = ""
    created_at_round: int = 1
    status: str = "PENDING_ROUND_EXECUTION"


@dataclass(frozen=True)
class ResourceTransferDirective:
    """Executive order or inter-role resource allocation directive within OMS powers."""

    transfer_id: str
    session_id: str
    sender_role_id: str
    recipient_role_id: str
    resources: dict[str, Decimal] = field(default_factory=dict)
    authorization_note: str = ""
    created_at_round: int = 1


@dataclass(frozen=True)
class RoleWorkspaceReadModel:
    """Aggregated role workspace read model including initial inventory, available balances, locked/reserved resources, psychological stress factors, and pending LEGO cards."""

    session_id: str
    role_id: str
    role_name: str
    initial_resources: dict[str, Decimal]
    available_resources: dict[str, Decimal]
    reserved_resources: dict[str, Decimal]
    pending_lego_cards: tuple[LegoDecisionCard, ...]
    active_directives: tuple[TaskDirective, ...]
    psychological_injects: tuple[PsychologicalFrictionInject, ...] = ()
    cognitive_stress_level_pct: float = 0.0
    capability_score: float = 100.0


class RoleDashboardService:
    """Manages role-scoped workspaces, initial resource inventories, psychological friction/stress injections, 100% resource exhaustion locking, open LEGO decision card assembly, and inter-role OMS resource transfers."""

    def __init__(self) -> None:
        # Structure: _session_resources[session_id][role_id] = {"initial": dict, "available": dict, "reserved": dict}
        self._session_resources: dict[str, dict[str, dict[str, dict[str, Decimal]]]] = {}
        self._pending_cards: dict[str, list[LegoDecisionCard]] = {}
        self._transfers: dict[str, list[ResourceTransferDirective]] = {}
        self._psychological_injects: dict[str, list[PsychologicalFrictionInject]] = {}

    def _ensure_role_initialized(self, session_id: str, role_id: str) -> None:
        if session_id not in self._session_resources:
            self._session_resources[session_id] = {}
            self._pending_cards[session_id] = []
            self._transfers[session_id] = []
            self._psychological_injects[session_id] = []

        if role_id not in self._session_resources[session_id]:
            defaults = ROLE_INITIAL_RESOURCES.get(
                role_id,
                {
                    "vehicles": Decimal("5"),
                    "personnel": Decimal("20"),
                    "fuel_liters": Decimal("1000"),
                    "generators": Decimal("2"),
                },
            )
            initial = {k: Decimal(str(v)) for k, v in defaults.items()}
            available = {k: Decimal(str(v)) for k, v in defaults.items()}
            reserved = {res_k: Decimal("0") for res_k in defaults.keys()}

            self._session_resources[session_id][role_id] = {
                "initial": initial,
                "available": available,
                "reserved": reserved,
            }

    def inject_psychological_friction(
        self,
        session_id: str,
        target_role_id: str,
        friction_type: str,
        title: str,
        description: str,
        stress_level_delta: float = 15.0,
        audio_siren_signal: bool = False,
        current_round: int = 1,
    ) -> PsychologicalFrictionInject:
        """Injects a psychological stress event (e.g. sirens, phone calls, social media trolls, protests, lost keys) into player dashboard."""
        self._ensure_role_initialized(session_id, target_role_id if target_role_id != "all_roles" else "head_of_emergency")

        inject = PsychologicalFrictionInject(
            inject_id=f"psych_{uuid4().hex[:8]}",
            session_id=session_id,
            target_role_id=target_role_id,
            friction_type=friction_type.strip().upper(),
            title=title.strip(),
            description=description.strip(),
            stress_level_delta=stress_level_delta,
            audio_siren_signal=audio_siren_signal,
            created_at_round=current_round,
        )

        self._psychological_injects[session_id].append(inject)
        return inject

    def get_role_workspace(
        self, session_id: str, role_id: str, active_directives: tuple[TaskDirective, ...] = ()
    ) -> RoleWorkspaceReadModel:
        self._ensure_role_initialized(session_id, role_id)
        role_res = self._session_resources[session_id][role_id]

        cards = [c for c in self._pending_cards.get(session_id, []) if c.role_id == role_id]
        psych_injects = [
            i
            for i in self._psychological_injects.get(session_id, [])
            if i.target_role_id in (role_id, "all_roles")
        ]

        total_stress = min(100.0, sum(i.stress_level_delta for i in psych_injects))

        role_name_map = {
            "head_of_emergency": "Голова ДСНС / Керівник штабу з НС",
            "chief_medical_officer": "Головний медичний офіцер громади",
            "chief_sanitary_inspector": "Головний санітарний інспектор",
            "chief_police_officer": "Керівник поліції громади",
            "chief_utility_officer": "Керівник комунальних служб",
        }

        return RoleWorkspaceReadModel(
            session_id=session_id,
            role_id=role_id,
            role_name=role_name_map.get(role_id, f"Оперативна роль ({role_id})"),
            initial_resources=dict(role_res["initial"]),
            available_resources=dict(role_res["available"]),
            reserved_resources=dict(role_res["reserved"]),
            pending_lego_cards=tuple(cards),
            active_directives=active_directives,
            psychological_injects=tuple(psych_injects),
            cognitive_stress_level_pct=total_stress,
            capability_score=max(0.0, 100.0 - (total_stress * 0.3)),
        )

    def submit_lego_decision_card(
        self,
        session_id: str,
        role_id: str,
        action_type: str,
        target_facility_id: str,
        allocated_resources: dict[str, Decimal],
        allocated_personnel: int = 0,
        custom_instructions: str = "",
        current_round: int = 1,
    ) -> LegoDecisionCard:
        if not action_type or not action_type.strip():
            raise DomainRuleViolation("LEGO decision card requires an action_type.")
        if not target_facility_id or not target_facility_id.strip():
            raise DomainRuleViolation("LEGO decision card requires a target_facility_id.")

        self._ensure_role_initialized(session_id, role_id)
        available = self._session_resources[session_id][role_id]["available"]
        reserved = self._session_resources[session_id][role_id]["reserved"]

        # Validate resource availability (allows allocating up to 100% of available balance)
        for res_key, req_qty in allocated_resources.items():
            current_avail = available.get(res_key, Decimal("0"))
            if req_qty < Decimal("0"):
                raise DomainRuleViolation(f"Resource quantity for '{res_key}' cannot be negative.")
            if req_qty > current_avail:
                raise DomainRuleViolation(
                    f"Insufficient '{res_key}' resources. Requested: {req_qty}, Available: {current_avail}."
                )

        # Lock/reserve allocated resources (deduct from available, add to reserved)
        for res_key, req_qty in allocated_resources.items():
            available[res_key] -= req_qty
            reserved[res_key] = reserved.get(res_key, Decimal("0")) + req_qty

        card = LegoDecisionCard(
            card_id=f"card_{uuid4().hex[:8]}",
            session_id=session_id,
            role_id=role_id,
            action_type=action_type.strip().upper(),
            target_facility_id=target_facility_id.strip(),
            allocated_resources=allocated_resources,
            allocated_personnel=allocated_personnel,
            custom_instructions=custom_instructions.strip(),
            created_at_round=current_round,
            status="PENDING_ROUND_EXECUTION",
        )

        self._pending_cards[session_id].append(card)
        return card

    def transfer_resources_oms(
        self,
        session_id: str,
        sender_role_id: str,
        recipient_role_id: str,
        resources: dict[str, Decimal],
        authorization_note: str = "",
        current_round: int = 1,
    ) -> ResourceTransferDirective:
        if sender_role_id == recipient_role_id:
            raise DomainRuleViolation("Sender and recipient roles must be different for resource transfer.")

        self._ensure_role_initialized(session_id, sender_role_id)
        self._ensure_role_initialized(session_id, recipient_role_id)

        sender_avail = self._session_resources[session_id][sender_role_id]["available"]
        recipient_avail = self._session_resources[session_id][recipient_role_id]["available"]
        recipient_init = self._session_resources[session_id][recipient_role_id]["initial"]

        # Validate sender has required resources
        for res_key, qty in resources.items():
            avail_qty = sender_avail.get(res_key, Decimal("0"))
            if qty <= Decimal("0"):
                raise DomainRuleViolation("Transfer quantity must be positive.")
            if qty > avail_qty:
                raise DomainRuleViolation(
                    f"Sender '{sender_role_id}' has insufficient '{res_key}'. Requested: {qty}, Available: {avail_qty}."
                )

        # Execute immediate transfer between role balances
        for res_key, qty in resources.items():
            sender_avail[res_key] -= qty
            recipient_avail[res_key] = recipient_avail.get(res_key, Decimal("0")) + qty
            recipient_init[res_key] = recipient_init.get(res_key, Decimal("0")) + qty

        transfer = ResourceTransferDirective(
            transfer_id=f"trans_{uuid4().hex[:8]}",
            session_id=session_id,
            sender_role_id=sender_role_id,
            recipient_role_id=recipient_role_id,
            resources=resources,
            authorization_note=authorization_note.strip(),
            created_at_round=current_round,
        )

        self._transfers[session_id].append(transfer)
        return transfer

    def resolve_round_execution(self, session_id: str, round_number: int) -> list[dict[str, Any]]:
        """Resolves all pending LEGO decision cards upon round advancement, clears reserved resources, and generates role-targeted outcome events."""
        if session_id not in self._pending_cards:
            return []

        pending_cards = self._pending_cards[session_id]
        outcomes: list[dict[str, Any]] = []

        for card in list(pending_cards):
            if card.status == "PENDING_ROUND_EXECUTION":
                # Clear reserved resources as consumed in the round
                if session_id in self._session_resources and card.role_id in self._session_resources[session_id]:
                    reserved = self._session_resources[session_id][card.role_id]["reserved"]
                    for res_key, req_qty in card.allocated_resources.items():
                        if res_key in reserved:
                            reserved[res_key] = max(Decimal("0"), reserved[res_key] - req_qty)

                outcomes.append(
                    {
                        "card_id": card.card_id,
                        "session_id": session_id,
                        "target_role_id": card.role_id,
                        "round_number": round_number,
                        "action_type": card.action_type,
                        "target_facility_id": card.target_facility_id,
                        "status": "EXECUTED_IN_ROUND",
                        "summary_report": f"Картку рішення LEGO «{card.action_type}» успішно виконано в раунді {round_number} на об'єкті {card.target_facility_id}.",
                    }
                )

        # Clear executed cards for this session
        self._pending_cards[session_id] = [c for c in pending_cards if c.status != "PENDING_ROUND_EXECUTION"]
        return outcomes
