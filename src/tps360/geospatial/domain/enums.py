from enum import StrEnum


class MapStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class LayerType(StrEnum):
    BASE_MAP = "base_map"
    ADMINISTRATIVE_BOUNDARY = "administrative_boundary"
    SETTLEMENTS = "settlements"
    ROADS = "roads"
    WATERWAYS = "waterways"
    BUILDINGS = "buildings"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    SHELTERS = "shelters"
    MEDICAL_FACILITIES = "medical_facilities"
    EDUCATION_FACILITIES = "education_facilities"
    WARNING_SYSTEMS = "warning_systems"
    RESOURCES = "resources"
    EVACUATION_ROUTES = "evacuation_routes"
    THREAT_ZONES = "threat_zones"
    IMPACT_ZONES = "impact_zones"
    SIMULATION_EVENTS = "simulation_events"
    TEAM_ACTIONS = "team_actions"


class AccessLevel(StrEnum):
    PUBLIC = "public"
    OPERATIONAL = "operational"
    RESTRICTED = "restricted"
    SENSITIVE = "sensitive"


class VerificationStatus(StrEnum):
    IMPORTED = "imported"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ARCHIVED = "archived"
