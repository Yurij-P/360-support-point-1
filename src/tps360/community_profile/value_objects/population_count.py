from dataclasses import dataclass


@dataclass(frozen=True)
class PopulationCount:
    value: int = 0

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("population")
