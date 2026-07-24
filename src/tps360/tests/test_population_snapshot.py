from datetime import date, timedelta

import pytest

from tps360.community_profile.domain import PopulationSnapshot
from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.community_profile.value_objects import PopulationCount


def build_snapshot(**overrides: object) -> PopulationSnapshot:
    values: dict[str, object] = {
        "total_population": PopulationCount(100),
        "children": PopulationCount(20),
        "older_people": PopulationCount(30),
        "persons_with_disabilities": PopulationCount(10),
        "internally_displaced_people": PopulationCount(5),
        "veterans": PopulationCount(7),
        "other_vulnerable_people": PopulationCount(3),
        "snapshot_date": date.today(),
        "evidence": ("registry",),
    }
    values.update(overrides)
    return PopulationSnapshot(**values)  # type: ignore[arg-type]


def test_population_snapshot_creation() -> None:
    snapshot = build_snapshot()

    assert snapshot.total_population == PopulationCount(100)
    assert snapshot.evidence == ("registry",)


def test_future_snapshot_date_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_snapshot(snapshot_date=date.today() + timedelta(days=1))


def test_children_exceeding_total_population_raises_error() -> None:
    with pytest.raises(ProfileRuleViolation):
        build_snapshot(children=PopulationCount(101))


def test_overlapping_groups_are_allowed() -> None:
    snapshot = build_snapshot(
        children=PopulationCount(70),
        older_people=PopulationCount(70),
        persons_with_disabilities=PopulationCount(70),
    )

    assert snapshot.aggregate_without_deduplication() == 225


def test_vulnerable_group_counts_returns_expected_values() -> None:
    assert build_snapshot().vulnerable_group_counts() == {
        "children": 20,
        "older_people": 30,
        "persons_with_disabilities": 10,
        "internally_displaced_people": 5,
        "veterans": 7,
        "other_vulnerable_people": 3,
    }


def test_aggregate_without_deduplication_returns_group_sum() -> None:
    assert build_snapshot().aggregate_without_deduplication() == 75