"""Command hierarchy authorization for task directives (ADR-0015).

Incident Command System over the KATOTTG role catalog:
- Facilitator (moderation) may issue to anyone.
- Commander (local-gov-head) may issue to command staff and functional leads.
- Chief of Staff (local-gov-civil-protection) may issue to functional leads.
- A functional lead may issue only to members of its own category.
- Members may not issue directives.
"""
from __future__ import annotations

from enum import StrEnum

from tps360.simulation.services.role_catalog_service import RoleCatalogService


class CommandTier(StrEnum):
    COMMANDER = "COMMANDER"
    COMMAND_STAFF = "COMMAND_STAFF"
    FUNCTIONAL_LEAD = "FUNCTIONAL_LEAD"
    MEMBER = "MEMBER"


# Roles that moderate the simulation and are outside the in-sim chain of command.
FACILITATOR_ROLE_IDS = frozenset({"facilitator", "facilitator_moderator", "system_admin"})

COMMANDER_ROLE_ID = "local-gov-head"
CHIEF_OF_STAFF_ROLE_ID = "local-gov-civil-protection"

_COMMAND_STAFF = frozenset(
    {"local-gov-civil-protection", "local-gov-deputy-head", "local-gov-executive-rep"}
)
_FUNCTIONAL_LEADS = frozenset(
    {
        "emerg-dsns",
        "emerg-police",
        "emerg-ems",
        "vol-fire-commander",
        "communal-utility",
        "communal-medical",
        "communal-social-service",
        "communal-child-services",
        "edu-director",
        "starost-district",
        "civil-humanitarian-hub",
        # Approved scenario role (TPS360-ROLE-UX-001 §5.2), treated as a functional lead.
        "chief_sanitary_inspector",
    }
)
_MEMBERS = frozenset(
    {
        "vol-fire-member",
        "edu-deputy-director",
        "edu-civil-protection",
        "edu-shelter-evac",
        "starost-remote-rep",
        "starost-info-coordinator",
        "civil-ngo",
        "civil-volunteer-group",
    }
)

_catalog = RoleCatalogService()


def tier_of(role_id: str) -> CommandTier | None:
    if role_id == COMMANDER_ROLE_ID:
        return CommandTier.COMMANDER
    if role_id in _COMMAND_STAFF:
        return CommandTier.COMMAND_STAFF
    if role_id in _FUNCTIONAL_LEADS:
        return CommandTier.FUNCTIONAL_LEAD
    if role_id in _MEMBERS:
        return CommandTier.MEMBER
    return None


def _category_of(role_id: str) -> str | None:
    entry = _catalog.get_entry(role_id)
    return entry.category_key if entry else None


def can_issue_directive(issuer_role_id: str, assignee_role_id: str) -> bool:
    """Return whether issuer may task assignee under the ICS command chain (ADR-0015)."""
    if issuer_role_id in FACILITATOR_ROLE_IDS:
        return True

    assignee_tier = tier_of(assignee_role_id)

    if issuer_role_id == COMMANDER_ROLE_ID:
        return assignee_tier in (CommandTier.COMMAND_STAFF, CommandTier.FUNCTIONAL_LEAD)

    if issuer_role_id == CHIEF_OF_STAFF_ROLE_ID:
        return assignee_tier is CommandTier.FUNCTIONAL_LEAD

    if tier_of(issuer_role_id) is CommandTier.FUNCTIONAL_LEAD:
        if assignee_tier is not CommandTier.MEMBER:
            return False
        issuer_cat = _category_of(issuer_role_id)
        return issuer_cat is not None and issuer_cat == _category_of(assignee_role_id)

    return False
