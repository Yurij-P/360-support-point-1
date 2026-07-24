from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..value_objects import (
    BoundingBox,
    Coordinates,
    PointGeometry,
    PolygonGeometry,
    SourceAttribution,
)
from .enums import AccessLevel, LayerType, MapStatus, VerificationStatus

Geometry = PointGeometry | PolygonGeometry


def now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class GeoFeature:
    layer_id: UUID
    name: str
    feature_type: str
    geometry: Geometry
    properties: dict[str, object] = field(default_factory=dict)
    external_source: str | None = None
    external_id: str | None = None
    access_level: AccessLevel = AccessLevel.PUBLIC
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    id: UUID = field(default_factory=uuid4)
    verified_at: datetime | None = None
    verified_by: str | None = None

    def __post_init__(self) -> None:
        if self.verification_status is VerificationStatus.IMPORTED and not (
            self.external_source and self.external_id
        ):
            raise ValueError("Imported feature requires source and id")

    def verify(self, by: str) -> None:
        self.verification_status = VerificationStatus.VERIFIED
        self.verified_by = by
        self.verified_at = now()

    def reject(self) -> None:
        self.verification_status = VerificationStatus.REJECTED

    def archive(self) -> None:
        self.verification_status = VerificationStatus.ARCHIVED

    def public_properties(self) -> dict[str, object]:
        return {
            k: (v.get("value") if isinstance(v, dict) else v)
            for k, v in self.properties.items()
            if not isinstance(v, dict) or v.get("access_level", "public") == "public"
        }


@dataclass
class MapLayer:
    community_map_id: UUID
    name: str
    layer_type: LayerType
    order: int = 0
    visibility: bool = True
    access_level: AccessLevel = AccessLevel.PUBLIC
    source: str | None = None
    features: list[GeoFeature] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.name.strip() or self.order < 0:
            raise ValueError("Invalid layer")

    def add_feature(self, f: GeoFeature) -> None:
        if f.layer_id != self.id or any(x.id == f.id for x in self.features):
            raise ValueError("Invalid feature")
        self.features.append(f)

    def public_features(self) -> list[dict[str, object]]:
        return [
            {
                "id": str(f.id),
                "name": f.name,
                "geometry": f.geometry.to_geojson(),
                "properties": f.public_properties(),
            }
            for f in self.features
            if f.access_level is AccessLevel.PUBLIC
        ]


@dataclass
class CommunityMap:
    community_id: UUID
    name: str
    boundary: PolygonGeometry | None = None
    center: Coordinates | None = None
    bounding_box: BoundingBox | None = None
    default_zoom: int = 12
    layers: list[MapLayer] = field(default_factory=list)
    source_attribution: SourceAttribution | None = None
    version: int = 1
    status: MapStatus = MapStatus.DRAFT
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.name.strip() or self.version < 1 or not 0 <= self.default_zoom <= 22:
            raise ValueError("Invalid map")

    def activate(self) -> None:
        if self.status is MapStatus.ARCHIVED or not self.boundary or not self.source_attribution:
            raise ValueError("Map cannot activate")
        self.status = MapStatus.ACTIVE

    def archive(self) -> None:
        self.status = MapStatus.ARCHIVED

    def add_layer(self, l: MapLayer) -> None:
        if l.community_map_id != self.id or any(x.id == l.id for x in self.layers):
            raise ValueError("Invalid layer")
        self.layers.append(l)

    def find_layer(self, i: UUID) -> MapLayer | None:
        return next((x for x in self.layers if x.id == i), None)

    def public_view(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "name": self.name,
            "layers": [
                {"id": str(l.id), "name": l.name, "features": l.public_features()}
                for l in self.layers
                if l.access_level is AccessLevel.PUBLIC
            ],
        }
