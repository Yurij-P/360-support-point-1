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

class DecisionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    FREE_TEXT = "free_text"
    RESOURCE_ALLOCATION = "resource_allocation"
    PRIORITIZATION = "prioritization"
    APPROVAL = "approval"
    COORDINATED = "coordinated"


class DecisionPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class DecisionRequestStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DecisionSubmissionStatus(StrEnum):
    SUBMITTED = "submitted"
    VALID = "valid"
    INVALID = "invalid"
    WITHDRAWN = "withdrawn"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class ApprovalRule(StrEnum):
    ALL = "all"
    ANY = "any"

class ImpactSourceType(StrEnum):
    EVENT = "event"
    DECISION = "decision"
    COMBINED = "combined"
    SYSTEM = "system"
    REVERSAL = "reversal"


class ImpactCategory(StrEnum):
    POPULATION = "population"
    TERRITORY = "territory"
    INFRASTRUCTURE = "infrastructure"
    RESOURCE = "resource"
    THREAT = "threat"
    SERVICE_CAPACITY = "service_capacity"
    COMMUNICATION = "communication"
    EVACUATION = "evacuation"
    HEALTH_AND_SAFETY = "health_and_safety"
    CUSTOM = "custom"


class ImpactTargetType(StrEnum):
    SIMULATION = "simulation"
    TERRITORY = "territory"
    SETTLEMENT = "settlement"
    POPULATION_GROUP = "population_group"
    INFRASTRUCTURE = "infrastructure"
    RESOURCE = "resource"
    THREAT = "threat"
    SERVICE = "service"
    CAPABILITY = "capability"


class ImpactOperation(StrEnum):
    SET = "set"
    INCREASE = "increase"
    DECREASE = "decrease"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    MIN = "min"
    MAX = "max"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    DAMAGE = "damage"
    RESTORE = "restore"
    CONSUME = "consume"
    REPLENISH = "replenish"
    LOCK = "lock"
    UNLOCK = "unlock"


class ImpactStatus(StrEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    READY = "ready"
    APPLIED = "applied"
    ACTIVE = "active"
    REVERSED = "reversed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ImpactConflictPolicy(StrEnum):
    REJECT = "reject"
    HIGHEST_PRIORITY = "highest_priority"
    SEQUENTIAL = "sequential"
    MERGE_ADDITIVE = "merge_additive"
    LAST_EXPLICIT_SET = "last_explicit_set"