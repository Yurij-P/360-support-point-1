from enum import StrEnum


class ThreatType(StrEnum):
    MILITARY = "military"
    TECHNOLOGICAL = "technological"
    NATURAL = "natural"
    MEDICAL_BIOLOGICAL = "medical_biological"
    SOCIAL_HUMANITARIAN = "social_humanitarian"
    CYBER_INFORMATION = "cyber_information"
    COMBINED = "combined"


class ThreatSeverity(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatImpact(StrEnum):
    HUMAN_LIFE = "human_life"
    HEALTH = "health"
    PROPERTY = "property"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    ESSENTIAL_SERVICES = "essential_services"
    ENVIRONMENT = "environment"
    ECONOMY = "economy"
    GOVERNANCE = "governance"
    INFORMATION_INTEGRITY = "information_integrity"


class ThreatTargetType(StrEnum):
    POPULATION = "population"
    SETTLEMENT = "settlement"
    FACILITY = "facility"
    ORGANIZATION = "organization"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    INFORMATION_SYSTEM = "information_system"
    ENVIRONMENT = "environment"