from tps360.simulation.services.command_hierarchy import (
    CommandTier,
    can_issue_directive,
    tier_of,
)


def test_tier_classification() -> None:
    assert tier_of("local-gov-head") is CommandTier.COMMANDER
    assert tier_of("local-gov-civil-protection") is CommandTier.COMMAND_STAFF
    assert tier_of("emerg-dsns") is CommandTier.FUNCTIONAL_LEAD
    assert tier_of("vol-fire-member") is CommandTier.MEMBER
    assert tier_of("unknown-role") is None


def test_facilitator_may_issue_to_anyone() -> None:
    assert can_issue_directive("facilitator", "emerg-dsns")
    assert can_issue_directive("facilitator_moderator", "vol-fire-member")
    assert can_issue_directive("facilitator", "any-scenario-role")


def test_commander_issues_to_staff_and_leads() -> None:
    assert can_issue_directive("local-gov-head", "local-gov-civil-protection")
    assert can_issue_directive("local-gov-head", "emerg-police")
    # not directly to a rank-and-file member
    assert not can_issue_directive("local-gov-head", "vol-fire-member")


def test_chief_of_staff_issues_only_to_functional_leads() -> None:
    assert can_issue_directive("local-gov-civil-protection", "communal-utility")
    assert not can_issue_directive("local-gov-civil-protection", "vol-fire-member")
    assert not can_issue_directive("local-gov-civil-protection", "local-gov-head")


def test_functional_lead_issues_only_to_own_category_members() -> None:
    # volunteer-fire commander -> volunteer-fire member (same category)
    assert can_issue_directive("vol-fire-commander", "vol-fire-member")
    # education director -> education members
    assert can_issue_directive("edu-director", "edu-shelter-evac")
    # cross-category is refused
    assert not can_issue_directive("edu-director", "vol-fire-member")
    # a lead may not task another lead
    assert not can_issue_directive("emerg-dsns", "emerg-police")


def test_members_cannot_issue() -> None:
    assert not can_issue_directive("vol-fire-member", "vol-fire-commander")
    assert not can_issue_directive("edu-shelter-evac", "edu-director")
