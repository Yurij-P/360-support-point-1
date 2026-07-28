"""Overpass API adapter — fetch REAL community infrastructure from OpenStreetMap.

Populates passport `infrastructure_items` with real OSM objects (hospitals, DSNS
stations, farms, pipelines, …) inside a community bounding box, replacing the
synthetic baseline. Free, keyless. Reuses the existing `OSM_TAG_MAPPINGS`
ontology (reverse lookup tag -> category). HTTP is injectable so tests are offline.

Overpass API: POST https://overpass-api.de/api/interpreter with an Overpass QL
body; response is JSON with an `elements` list (nodes/ways; ways carry `center`).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any, cast

from tps360.community.domain.infrastructure_taxonomy import (
    OSM_TAG_MAPPINGS,
    CriticalInfrastructureCategory,
)
from tps360.community.domain.passport_read_model import InfrastructureItemReadModel

_BASE = "https://overpass-api.de/api/interpreter"

# Reverse lookup: (osm_key, osm_value) -> category.
_TAG_TO_CATEGORY: dict[tuple[str, str], CriticalInfrastructureCategory] = {
    (m.osm_key, m.osm_value): cat for cat, m in OSM_TAG_MAPPINGS.items()
}


def _http_post_json(query: str) -> dict[str, Any]:
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(_BASE, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return cast("dict[str, Any]", json.loads(resp.read().decode("utf-8")))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Overpass HTTP {exc.code}: {exc.reason}") from exc


def build_query(south: float, west: float, north: float, east: float) -> str:
    box = f"({south},{west},{north},{east})"
    clauses = []
    for key, value in _TAG_TO_CATEGORY:
        clauses.append(f'node["{key}"="{value}"]{box};')
        clauses.append(f'way["{key}"="{value}"]{box};')
    return f"[out:json][timeout:25];({''.join(clauses)});out center;"


class OverpassClient:
    def __init__(self, fetch: Callable[[str], dict[str, Any]] | None = None) -> None:
        self._fetch = fetch or _http_post_json

    def fetch_elements(
        self, south: float, west: float, north: float, east: float
    ) -> list[dict[str, Any]]:
        data = self._fetch(build_query(south, west, north, east))
        elements = data.get("elements", [])
        return elements if isinstance(elements, list) else []


def elements_to_infrastructure(
    elements: list[dict[str, Any]],
) -> list[InfrastructureItemReadModel]:
    """Map raw Overpass elements to passport infrastructure items via the ontology."""
    items: list[InfrastructureItemReadModel] = []
    for element in elements:
        tags = element.get("tags", {})
        matched: tuple[str, str] | None = None
        for key, value in _TAG_TO_CATEGORY:
            if tags.get(key) == value:
                matched = (key, value)
                break
        if matched is None:
            continue

        lat = element.get("lat")
        lon = element.get("lon")
        if lat is None or lon is None:
            center = element.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if lat is None or lon is None:
            continue

        category = _TAG_TO_CATEGORY[matched]
        items.append(
            InfrastructureItemReadModel(
                id=f"osm_{element.get('type', 'node')}_{element.get('id')}",
                name=tags.get("name") or category.value,
                category=category,
                latitude=float(lat),
                longitude=float(lon),
                osm_key=matched[0],
                osm_value=matched[1],
            )
        )
    return items
