from dataclasses import dataclass


@dataclass(frozen=True)
class Capacity:
    value: float = 0
    unit: str = "persons"

    def __post_init__(self) -> None:
        if self.value < 0 or not self.unit.strip():
            raise ValueError("capacity")
