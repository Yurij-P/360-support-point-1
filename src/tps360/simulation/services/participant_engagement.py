"""Participant-aware crisis coverage (TPS360-SCEN-GEN-001).

Given the present session roster and a hazard, determine which roles the crisis
naturally engages, which are idle, and the secondary condition that pulls each
idle role into an action. Goal: zero passive roles (100% coverage). Relevance
and secondary-condition maps are provisional placeholders.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from tps360.simulation.services.crisis_demand import hazard_family

# Command / territorial roles act regardless of hazard family.
_ALWAYS_ENGAGED = frozenset(
    {
        "local-gov-head",
        "local-gov-deputy-head",
        "local-gov-civil-protection",
        "local-gov-executive-rep",
        "starost-district",
    }
)

# Hazard family -> roles whose core function that family engages (provisional).
_FAMILY_ROLES: dict[str, set[str]] = {
    "fire": {"emerg-dsns", "vol-fire-commander", "vol-fire-member", "emerg-ems"},
    "flood": {"emerg-dsns", "communal-utility", "emerg-ems"},
    "chemical": {"chief_sanitary_inspector", "communal-medical", "emerg-ems", "emerg-dsns"},
    "radiation": {"chief_sanitary_inspector", "communal-medical", "emerg-ems"},
    "utility": {"communal-utility", "communal-social-service"},
    "strike": {"emerg-dsns", "emerg-police", "emerg-ems"},
    "epidemic": {
        "chief_sanitary_inspector",
        "communal-medical",
        "emerg-ems",
        "communal-social-service",
    },
    "generic": {"emerg-dsns", "emerg-police", "emerg-ems", "communal-utility"},
}

# Idle role -> secondary condition that engages it (provisional, SCEN-GEN-001 §4-5).
_SECONDARY_CONDITION: dict[str, str] = {
    "edu-director": "Заклад освіти розгортається як пункт евакуації/укриття.",
    "edu-deputy-director": "Організація укриття та переклички у закладі освіти.",
    "edu-civil-protection": "Відповідальність за цивільний захист у закладі освіти.",
    "edu-shelter-evac": "Керування евакуацією/укриттям у закладі освіти.",
    "communal-child-services": "Облік і супровід дітей у зоні НС.",
    "communal-social-service": "Соціальний супровід вразливих груп під час НС.",
    "civil-ngo": "Залучення ГО до інформування та допомоги населенню.",
    "civil-volunteer-group": "Волонтерська логістика та роздача допомоги.",
    "civil-humanitarian-hub": "Розгортання гуманітарного штабу громади.",
    "starost-remote-rep": "Первинний збір інформації з віддаленого населеного пункту.",
    "starost-info-coordinator": "Координація збору інформації з території.",
}
_GENERIC_SECONDARY = "Залучення ролі через додаткову умову сценарію (координація/підтримка)."


def engaged_roles(hazard_type: str, roster: Iterable[str]) -> set[str]:
    core = _FAMILY_ROLES.get(hazard_family(hazard_type), set())
    return {r for r in roster if r in _ALWAYS_ENGAGED or r in core}


def idle_roles(hazard_type: str, roster: Iterable[str]) -> list[str]:
    engaged = engaged_roles(hazard_type, roster)
    return [r for r in roster if r not in engaged]


def secondary_condition_for(role_id: str) -> str:
    return _SECONDARY_CONDITION.get(role_id, _GENERIC_SECONDARY)


@dataclass(frozen=True)
class CoveragePlan:
    hazard_type: str
    engaged: tuple[str, ...]
    idle: tuple[str, ...]
    secondary_conditions: dict[str, str]
    coverage_pct: float


def build_coverage_plan(hazard_type: str, roster: Iterable[str]) -> CoveragePlan:
    """Coverage plan for a crisis; idle roles get a secondary condition (guard -> 100%)."""
    unique = list(dict.fromkeys(roster))  # dedupe, preserve order
    engaged_set = engaged_roles(hazard_type, unique)
    engaged = [r for r in unique if r in engaged_set]
    idle = [r for r in unique if r not in engaged_set]
    secondary = {r: secondary_condition_for(r) for r in idle}

    covered = len(engaged) + len(secondary)  # every idle role gets a condition
    coverage_pct = 100.0 if not unique else round(100.0 * covered / len(unique), 1)
    return CoveragePlan(
        hazard_type=hazard_type,
        engaged=tuple(engaged),
        idle=tuple(idle),
        secondary_conditions=secondary,
        coverage_pct=coverage_pct,
    )
