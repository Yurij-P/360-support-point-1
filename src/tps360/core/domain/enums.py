from enum import StrEnum


class HazardCategory(StrEnum):
    NATURAL = "natural"
    TECHNOLOGICAL = "technological"
    BIOLOGICAL = "biological"
    SOCIAL = "social"
    MILITARY = "military"
    CYBER = "cyber"
    COMBINED = "combined"


class CapabilityDomain(StrEnum):
    GOVERNANCE = "governance"
    RISK_ASSESSMENT = "risk_assessment"
    PLANNING = "planning"
    COORDINATION = "coordination"
    WARNING = "warning"
    COMMUNICATION = "communication"
    EVACUATION = "evacuation"
    SHELTER = "shelter"
    MEDICAL_RESPONSE = "medical_response"
    LOGISTICS = "logistics"
    INFRASTRUCTURE = "infrastructure"
    CYBERSECURITY = "cybersecurity"
    RECOVERY = "recovery"
    COMMUNITY_ENGAGEMENT = "community_engagement"


class LifecycleStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class MaturityLevel(StrEnum):
    REACTIVE = "reactive"
    BASIC = "basic"
    MANAGED = "managed"
    INTEGRATED = "integrated"
    RESILIENT = "resilient"
