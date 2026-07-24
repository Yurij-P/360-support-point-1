from dataclasses import dataclass
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation


@dataclass(frozen=True)
class Scenario:
    """A named exercise context for a simulation."""

    id: UUID
    name: str
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainRuleViolation("Scenario name must not be empty.")
        if not self.description.strip():
            raise DomainRuleViolation("Scenario description must not be empty.")