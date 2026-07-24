from dataclasses import dataclass

from .coordinates import Coordinates


@dataclass(frozen=True)
class BoundingBox:
    south: float
    west: float
    north: float
    east: float

    def __post_init__(self) -> None:
        if not (-90 <= self.south < self.north <= 90 and -180 <= self.west < self.east <= 180):
            raise ValueError("Invalid bounding box")

    def contains(self, p: Coordinates) -> bool:
        return self.south <= p.latitude <= self.north and self.west <= p.longitude <= self.east
