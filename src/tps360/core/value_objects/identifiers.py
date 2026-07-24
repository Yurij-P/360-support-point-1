from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4


@dataclass(frozen=True)
class _Identifier:
    value: UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


class CommunityId(_Identifier):
    pass


class ScenarioId(_Identifier):
    pass


class SimulationId(_Identifier):
    pass


class AssessmentId(_Identifier):
    pass
