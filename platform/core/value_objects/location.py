from dataclasses import dataclass


@dataclass(frozen=True)
class GeoLocation:
    latitude: float
    longitude: float
    label: str | None = None

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90 or not -180 <= self.longitude <= 180:
            raise ValueError("Coordinates are outside geographic bounds")
