from dataclasses import dataclass

from tps360.core.exceptions import DomainRuleViolation


@dataclass(frozen=True)
class ScenarioMetadata:
    author: str
    source: str

    def __post_init__(self) -> None:
        if not self.author.strip() or not self.source.strip():
            raise DomainRuleViolation("Scenario metadata author and source must not be empty.")