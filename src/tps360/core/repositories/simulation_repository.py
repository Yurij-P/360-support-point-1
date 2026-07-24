from uuid import UUID

from tps360.core.domain.models import Simulation
from tps360.core.exceptions import NotFoundError


class SimulationRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Simulation] = {}

    def add(self, item: Simulation) -> Simulation:
        self.items[item.id] = item
        return item

    def get(self, item_id: UUID) -> Simulation:
        if item_id not in self.items:
            raise NotFoundError("Simulation not found")
        return self.items[item_id]
