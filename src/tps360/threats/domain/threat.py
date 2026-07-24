from dataclasses import dataclass
from uuid import UUID

from tps360.core.exceptions import DomainRuleViolation

from .enums import ThreatImpact, ThreatSeverity, ThreatTargetType, ThreatType


@dataclass
class Threat:
    """A standalone description of a threat, without scenario or target instances."""

    id: UUID
    name: str
    threat_type: ThreatType
    severity: ThreatSeverity
    target_type: ThreatTargetType
    description: str
    impacts: tuple[ThreatImpact, ...] = ()
    is_active: bool = True
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainRuleViolation("Threat name must not be empty.")
        if not self.description.strip():
            raise DomainRuleViolation("Threat description must not be empty.")
        if len(set(self.impacts)) != len(self.impacts):
            raise DomainRuleViolation("Threat impacts must not contain duplicates.")
        if any(not item.strip() for item in self.evidence):
            raise DomainRuleViolation("Threat evidence must not contain empty strings.")

    def has_impact(self, impact: ThreatImpact) -> bool:
        return impact in self.impacts

    def is_critical(self) -> bool:
        return self.severity is ThreatSeverity.CRITICAL

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False