from dataclasses import dataclass
from enum import StrEnum


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class Score:
    """A 0–100 score; its interpretation requires an explicitly named scale."""

    value: float
    scale: str

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError("Score value must be between 0 and 100")
        if not self.scale.strip():
            raise ValueError("Score scale must be explicitly named")
