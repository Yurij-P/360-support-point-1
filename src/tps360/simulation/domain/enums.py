from enum import StrEnum


class SimulationStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ScenarioType(StrEnum):
    MILITARY = "military"
    TECHNOLOGICAL = "technological"
    NATURAL = "natural"
    HUMANITARIAN = "humanitarian"
    COMBINED = "combined"


class ScenarioDifficulty(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class ScenarioRuntimeStatus(StrEnum):
    LOADED = "loaded"
    VALIDATED = "validated"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScenarioValidationLevel(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class ScheduledEventType(StrEnum):
    TIME_BASED = "time_based"
    CONDITION_BASED = "condition_based"
    DEPENDENCY_BASED = "dependency_based"
    MANUAL = "manual"
    RECURRING = "recurring"


class EventPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class EventRuntimeStatus(StrEnum):
    SCHEDULED = "scheduled"
    BLOCKED = "blocked"
    READY = "ready"
    ACTIVE = "active"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"


class DependencyRule(StrEnum):
    ALL = "all"
    ANY = "any"


class ActivationConditionType(StrEnum):
    PHASE_IS = "phase_is"
    EVENT_STATUS_IS = "event_status_is"
    STATE_VALUE_EQUALS = "state_value_equals"
    ACTIVE_THREAT_PRESENT = "active_threat_present"
    TERRITORY_AVAILABLE = "territory_available"
    INFRASTRUCTURE_AVAILABLE = "infrastructure_available"
    RESOURCE_AVAILABLE = "resource_available"