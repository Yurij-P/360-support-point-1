from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class DataQuality:
    completeness_score: float
    verification_score: float
    freshness_score: float
    confidence_level: str
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    last_reviewed_at: datetime | None = None

    def __post_init__(self) -> None:
        if any(
            not 0 <= x <= 100
            for x in (self.completeness_score, self.verification_score, self.freshness_score)
        ):
            raise ValueError("score")
