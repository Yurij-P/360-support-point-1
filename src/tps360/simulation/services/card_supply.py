"""LEGO decision-card supply engine (TPS360-LEGO-001).

Cards are supplied contextually, not as an obvious right answer:
- a starting hand sized by command tier (commander widest);
- per-round drip of a small subset tied to the active crisis branch;
- anti-guessing distractors (plausible but sub-optimal cards) in each offer;
- liquidation cards appear only as the branch escalates.

Selection is deterministic (hashed by role/hazard/round) for reproducibility.
Card templates and coefficients are provisional placeholders.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from tps360.simulation.services.command_hierarchy import CommandTier, tier_of
from tps360.simulation.services.crisis_demand import hazard_family

# Severity at/above which the branch is "escalating" and liquidation cards appear.
ESCALATION_SEVERITY = 0.5


@dataclass(frozen=True)
class DecisionCardTemplate:
    action_type: str
    families: frozenset[str]
    is_liquidation: bool = False


_CATALOG: tuple[DecisionCardTemplate, ...] = (
    DecisionCardTemplate("EXTINGUISH_FIRE", frozenset({"fire"}), is_liquidation=True),
    DecisionCardTemplate("CONTAIN", frozenset({"fire", "chemical", "radiation"})),
    DecisionCardTemplate("EVACUATE", frozenset({"fire", "flood", "strike", "radiation"})),
    DecisionCardTemplate("DEPLOY_SHELTER", frozenset({"strike", "flood", "generic"})),
    DecisionCardTemplate("REPAIR_LINE", frozenset({"utility"}), is_liquidation=True),
    DecisionCardTemplate("DECONTAMINATE", frozenset({"chemical", "radiation"}), is_liquidation=True),
    DecisionCardTemplate("ISOLATE_QUARANTINE", frozenset({"epidemic"}), is_liquidation=True),
    DecisionCardTemplate("DISTRIBUTE_SUPPLIES", frozenset({"flood", "epidemic", "generic"})),
    DecisionCardTemplate("ESTABLISH_TRIAGE", frozenset({"strike", "epidemic", "chemical"})),
    DecisionCardTemplate("PATROL_SECURE", frozenset({"strike", "generic"})),
)

_TIER_HAND_SIZE = {
    CommandTier.COMMANDER: 8,
    CommandTier.COMMAND_STAFF: 6,
    CommandTier.FUNCTIONAL_LEAD: 4,
    CommandTier.MEMBER: 2,
}
_DEFAULT_HAND_SIZE = 3


def _stable_index(seed: str, modulo: int) -> int:
    if modulo <= 0:
        return 0
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
    return int(digest, 16) % modulo


def _relevant(family: str) -> list[DecisionCardTemplate]:
    return [c for c in _CATALOG if family in c.families]


def _distractors(family: str) -> list[DecisionCardTemplate]:
    # Plausible but off-family cards (never absurd): everything not in this family.
    return [c for c in _CATALOG if family not in c.families]


def _rotate(cards: list[DecisionCardTemplate], seed: str) -> list[DecisionCardTemplate]:
    if not cards:
        return []
    ordered = sorted(cards, key=lambda c: c.action_type)
    start = _stable_index(seed, len(ordered))
    return ordered[start:] + ordered[:start]


def initial_hand(role_id: str, hazard_type: str) -> list[str]:
    """Starting hand of action types, sized by command tier (commander widest)."""
    family = hazard_family(hazard_type)
    tier = tier_of(role_id)
    size = _TIER_HAND_SIZE[tier] if tier is not None else _DEFAULT_HAND_SIZE
    relevant = _rotate(_relevant(family), f"{role_id}|{hazard_type}|hand")
    hand = [c.action_type for c in relevant[:size]]
    # anti-guessing: mix in one plausible distractor so the hand is not a giveaway
    distractors = _rotate(_distractors(family), f"{role_id}|{hazard_type}|hand-d")
    if distractors and len(hand) < max(2, size):
        hand.append(distractors[0].action_type)
    return hand


@dataclass(frozen=True)
class RoundOffer:
    offered: tuple[str, ...]
    includes_liquidation: bool


def round_offer(
    role_id: str, hazard_type: str, round_number: int, branch_severity: float
) -> RoundOffer:
    """Drip a small branch-tied subset for the round, with distractors and (on
    escalation) liquidation cards. Never a single obvious card."""
    family = hazard_family(hazard_type)
    seed = f"{role_id}|{hazard_type}|{round_number}"

    escalating = branch_severity >= ESCALATION_SEVERITY
    non_liq = [c for c in _relevant(family) if not c.is_liquidation]
    liq = [c for c in _relevant(family) if c.is_liquidation]

    picked: list[str] = []
    rotated = _rotate(non_liq, seed)
    if rotated:
        picked.append(rotated[0].action_type)

    # one distractor keeps the choice non-trivial (anti-guessing)
    distractors = _rotate(_distractors(family), seed + "|d")
    if distractors:
        picked.append(distractors[0].action_type)

    # liquidation cards only once the branch is escalating
    includes_liquidation = False
    if escalating and liq:
        picked.append(_rotate(liq, seed + "|liq")[0].action_type)
        includes_liquidation = True

    # de-duplicate, preserve order
    offered = tuple(dict.fromkeys(picked))
    return RoundOffer(offered=offered, includes_liquidation=includes_liquidation)
