from typing import Any

from tps360.community.domain.infrastructure_taxonomy import CriticalInfrastructureCategory
from tps360.community.services.osm_overpass import (
    OverpassClient,
    build_query,
    elements_to_infrastructure,
)


def test_build_query_contains_bbox_and_tags() -> None:
    q = build_query(48.0, 31.0, 48.5, 31.5)
    assert "[out:json]" in q
    assert "(48.0,31.0,48.5,31.5)" in q
    assert 'node["military"="base"]' in q  # a known ontology tag
    assert q.strip().endswith("out center;")


def test_fetch_elements_passes_query_and_returns_list() -> None:
    seen: dict[str, str] = {}

    def fetch(query: str) -> dict[str, Any]:
        seen["q"] = query
        return {"elements": [{"type": "node", "id": 1, "lat": 48.1, "lon": 31.1, "tags": {}}]}

    client = OverpassClient(fetch=fetch)
    els = client.fetch_elements(48.0, 31.0, 48.5, 31.5)
    assert len(els) == 1
    assert "military" in seen["q"]


def test_elements_to_infrastructure_maps_ontology() -> None:
    elements = [
        # node with a mapped tag
        {"type": "node", "id": 10, "lat": 48.2, "lon": 31.2,
         "tags": {"military": "base", "name": "База"}},
        # way with center (no lat/lon)
        {"type": "way", "id": 20, "center": {"lat": 48.3, "lon": 31.3},
         "tags": {"military": "airfield"}},
        # unmapped tag -> skipped
        {"type": "node", "id": 30, "lat": 48.4, "lon": 31.4, "tags": {"shop": "bakery"}},
        # mapped but missing coordinates -> skipped
        {"type": "node", "id": 40, "tags": {"military": "base"}},
    ]
    items = elements_to_infrastructure(elements)
    assert len(items) == 2
    first = items[0]
    assert first.category is CriticalInfrastructureCategory.MILITARY_BASE
    assert first.name == "База"
    assert first.osm_key == "military" and first.osm_value == "base"
    assert items[1].latitude == 48.3  # taken from way center
