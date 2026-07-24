from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EvidenceReference:
    source: str
    reference: str
    collected_on: date | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.reference.strip():
            raise ValueError("Evidence source and reference are required")
