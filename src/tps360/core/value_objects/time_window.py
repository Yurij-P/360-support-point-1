from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimeWindow:
    starts_at: datetime
    ends_at: datetime

    def __post_init__(self) -> None:
        if self.ends_at <= self.starts_at:
            raise ValueError("Time window must end after it starts")
