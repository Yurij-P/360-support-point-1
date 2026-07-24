from dataclasses import dataclass

from .coordinates import Coordinates


@dataclass(frozen=True)
class PointGeometry:
    coordinates: Coordinates

    def to_geojson(self) -> dict[str, object]:
        return {"type": "Point", "coordinates": self.coordinates.to_geojson_position()}


@dataclass(frozen=True)
class LineStringGeometry:
    coordinates: tuple[Coordinates, ...]

    def __post_init__(self) -> None:
        if len(self.coordinates) < 2:
            raise ValueError("LineString needs two points")

    def to_geojson(self) -> dict[str, object]:
        return {
            "type": "LineString",
            "coordinates": [p.to_geojson_position() for p in self.coordinates],
        }


@dataclass(frozen=True)
class PolygonGeometry:
    coordinates: tuple[Coordinates, ...]

    def __post_init__(self) -> None:
        if len(self.coordinates) < 4 or self.coordinates[0] != self.coordinates[-1]:
            raise ValueError("Polygon must be closed")

    def to_geojson(self) -> dict[str, object]:
        return {
            "type": "Polygon",
            "coordinates": [[p.to_geojson_position() for p in self.coordinates]],
        }


@dataclass(frozen=True)
class MultiPolygonGeometry:
    polygons: tuple[PolygonGeometry, ...]

    def __post_init__(self) -> None:
        if not self.polygons:
            raise ValueError("MultiPolygon needs polygon")

    def to_geojson(self) -> dict[str, object]:
        return {
            "type": "MultiPolygon",
            "coordinates": [p.to_geojson()["coordinates"] for p in self.polygons],
        }
