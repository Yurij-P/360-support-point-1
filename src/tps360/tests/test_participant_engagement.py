from tps360.simulation.services.participant_engagement import (
    build_coverage_plan,
    engaged_roles,
    idle_roles,
)


def test_field_fire_engages_dsns_not_school_directors() -> None:
    roster = ["emerg-dsns", "edu-director", "edu-deputy-director"]
    engaged = engaged_roles("wildfire", roster)
    assert "emerg-dsns" in engaged
    assert "edu-director" not in engaged


def test_idle_roles_get_secondary_conditions() -> None:
    roster = ["emerg-dsns", "edu-director"]
    plan = build_coverage_plan("wildfire", roster)
    assert "edu-director" in plan.idle
    assert plan.secondary_conditions["edu-director"]  # non-empty condition text


def test_coverage_is_full_after_secondary_conditions() -> None:
    # 7 participants incl 2 school directors + field fire -> nobody passive
    roster = [
        "local-gov-head",
        "emerg-dsns",
        "emerg-police",
        "emerg-ems",
        "edu-director",
        "edu-deputy-director",
        "communal-utility",
    ]
    plan = build_coverage_plan("wildfire", roster)
    assert plan.coverage_pct == 100.0
    # every present role is either engaged or has a secondary condition
    accounted = set(plan.engaged) | set(plan.secondary_conditions)
    assert accounted == set(roster)


def test_command_role_always_engaged() -> None:
    assert "local-gov-head" in engaged_roles("blackout", ["local-gov-head"])


def test_roster_deduped() -> None:
    plan = build_coverage_plan("wildfire", ["emerg-dsns", "emerg-dsns"])
    assert len(plan.engaged) == 1


def test_empty_roster_is_vacuously_covered() -> None:
    assert build_coverage_plan("wildfire", []).coverage_pct == 100.0
    assert idle_roles("wildfire", []) == []
