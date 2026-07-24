from datetime import date
from uuid import uuid4

import pytest

from tps360.geospatial.domain.enums import AccessLevel, LayerType, MapStatus, VerificationStatus
from tps360.geospatial.domain.models import CommunityMap, GeoFeature, MapLayer
from tps360.geospatial.repositories import CommunityMapRepository
from tps360.geospatial.services import MapService
from tps360.geospatial.value_objects import (
    BoundingBox,
    Coordinates,
    LineStringGeometry,
    MultiPolygonGeometry,
    PointGeometry,
    PolygonGeometry,
    SourceAttribution,
)


def point():
    return Coordinates(50, 30)


def polygon():
    p = point()
    return PolygonGeometry((p, Coordinates(50, 31), Coordinates(51, 31), p))


def attribution():
    return SourceAttribution(
        "OpenStreetMap",
        "ODbL",
        "© OpenStreetMap contributors",
        "https://www.openstreetmap.org",
        date.today(),
    )


def cmap():
    return CommunityMap(
        community_id=uuid4(), name="Map", boundary=polygon(), source_attribution=attribution()
    )


@pytest.mark.parametrize("lat,lon", [(0, 0), (90, 180), (-90, -180)])
def test_coordinates_valid(lat, lon):
    assert Coordinates(lat, lon).to_geojson_position() == [lon, lat]


@pytest.mark.parametrize("lat,lon", [(91, 0), (-91, 0), (0, 181), (0, -181)])
def test_coordinates_invalid(lat, lon):
    with pytest.raises(ValueError):
        Coordinates(lat, lon)


def test_linestring_requires_two():
    with pytest.raises(ValueError):
        LineStringGeometry((point(),))


def test_polygon_requires_closure():
    with pytest.raises(ValueError):
        PolygonGeometry((point(), Coordinates(1, 1), Coordinates(2, 2), Coordinates(3, 3)))


def test_polygon_geojson():
    assert polygon().to_geojson()["type"] == "Polygon"


def test_multipolygon():
    assert MultiPolygonGeometry((polygon(),)).to_geojson()["type"] == "MultiPolygon"


def test_bbox_invalid():
    with pytest.raises(ValueError):
        BoundingBox(2, 0, 1, 1)


def test_bbox_contains():
    assert BoundingBox(49, 29, 51, 31).contains(point())


def test_attribution_empty():
    with pytest.raises(ValueError):
        SourceAttribution("", "", "", "", date.today())


def test_osm_requires_attribution():
    with pytest.raises(ValueError):
        SourceAttribution("OpenStreetMap", "x", "x", "url", date.today())


def test_imported_feature_requires_id():
    with pytest.raises(ValueError):
        GeoFeature(
            layer_id=uuid4(),
            name="x",
            feature_type="x",
            geometry=PointGeometry(point()),
            verification_status=VerificationStatus.IMPORTED,
            external_source="osm",
        )


def test_feature_lifecycle_and_public_properties():
    f = GeoFeature(
        layer_id=uuid4(),
        name="x",
        feature_type="x",
        geometry=PointGeometry(point()),
        properties={"a": 1, "secret": {"value": "x", "access_level": "sensitive"}},
    )
    f.verify("u")
    assert f.verified_by == "u" and f.public_properties() == {"a": 1}
    f.reject()
    assert f.verification_status is VerificationStatus.REJECTED
    f.archive()
    assert f.verification_status is VerificationStatus.ARCHIVED


def test_layer_rules():
    with pytest.raises(ValueError):
        MapLayer(community_map_id=uuid4(), name="x", layer_type=LayerType.ROADS, order=-1)


def test_layer_duplicate_feature():
    l = MapLayer(community_map_id=uuid4(), name="x", layer_type=LayerType.ROADS)
    f = GeoFeature(layer_id=l.id, name="x", feature_type="x", geometry=PointGeometry(point()))
    l.add_feature(f)
    with pytest.raises(ValueError):
        l.add_feature(f)


def test_map_activation_rules():
    m = CommunityMap(community_id=uuid4(), name="x")
    with pytest.raises(ValueError):
        m.activate()


def test_archived_map_cannot_activate():
    m = cmap()
    m.archive()
    with pytest.raises(ValueError):
        m.activate()


def test_duplicate_layer():
    m = cmap()
    l = MapLayer(community_map_id=m.id, name="x", layer_type=LayerType.ROADS)
    m.add_layer(l)
    with pytest.raises(ValueError):
        m.add_layer(l)


def test_public_view_filters_layers():
    m = cmap()
    m.add_layer(
        MapLayer(
            community_map_id=m.id,
            name="s",
            layer_type=LayerType.ROADS,
            access_level=AccessLevel.SENSITIVE,
        )
    )
    assert m.public_view()["layers"] == []


def test_repository_rules_and_service():
    r = CommunityMapRepository()
    s = MapService(r)
    m = cmap()
    s.create_map(m)
    s.activate_map_version(m)
    assert r.get_active_by_community(m.community_id) == m
    with pytest.raises(ValueError):
        r.add(m)


def test_only_one_active_map():
    r = CommunityMapRepository()
    a = cmap()
    r.add(a)
    a.activate()
    r.save(a)
    b = cmap()
    b.community_id = a.community_id
    r.add(b)
    b.activate()
    r.save(b)
    assert a.status is MapStatus.ARCHIVED and b.status is MapStatus.ACTIVE
