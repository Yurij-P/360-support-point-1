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