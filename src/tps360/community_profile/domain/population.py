from dataclasses import dataclass
from datetime import date

from tps360.community_profile.exceptions import ProfileRuleViolation
from tps360.community_profile.value_objects import PopulationCount


@dataclass
class PopulationSnapshot:
    """Population counts recorded for a particular date."""

    total_population: PopulationCount
    children: PopulationCount
    older_people: PopulationCount
    persons_with_disabilities: PopulationCount
    internally_displaced_people: PopulationCount
    veterans: PopulationCount
    other_vulnerable_people: PopulationCount
    snapshot_date: date
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.snapshot_date > date.today():
            raise ProfileRuleViolation("Snapshot date must not be in the future.")
        if any(count.value > self.total_population.value for count in self._group_counts()):
            raise ProfileRuleViolation("A population group must not exceed the total population.")
        if any(not item.strip() for item in self.evidence):
            raise ProfileRuleViolation("Population evidence must not contain empty strings.")

    def vulnerable_group_counts(self) -> dict[str, int]:
        return {
            "children": self.children.value,
            "older_people": self.older_people.value,
            "persons_with_disabilities": self.persons_with_disabilities.value,
            "internally_displaced_people": self.internally_displaced_people.value,
            "veterans": self.veterans.value,
            "other_vulnerable_people": self.other_vulnerable_people.value,
        }

    def aggregate_without_deduplication(self) -> int:
        """Return the sum of groups without removing overlaps; it is not a unique-person count."""
        return sum(self.vulnerable_group_counts().values())

    def _group_counts(self) -> tuple[PopulationCount, ...]:
        return (
            self.children,
            self.older_people,
            self.persons_with_disabilities,
            self.internally_displaced_people,
            self.veterans,
            self.other_vulnerable_people,
        )