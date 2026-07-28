"""Clarity Project open-API adapter for real communal-enterprise data (Phase 2).

Feeds the endowment estimator with real entities and real vehicle fleet instead
of pure normative estimates (TPS360-RES-001 §5.1, source: registry).

Clarity Project API: GET https://clarity-project.info/api/{method}?key=...&...
Relevant methods: `edr.info` (legal entities / ФОП), `vehicles.list` (vehicles).
The key is read from CLARITY_API_KEY. HTTP is injectable so tests never hit the
network. Response parsing is best-effort and tolerant of shape changes.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections.abc import Callable
from decimal import Decimal
from typing import Any, cast

_BASE = "https://clarity-project.info/api"

# Provisional: how a raw Clarity vehicle record maps to an endowment resource key.
_VEHICLE_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("трактор", "tractors"),
    ("асеніз", "sewage_trucks"),
    ("автоцистерн", "water_tankers"),
    ("пожеж", "fire_trucks"),
    ("швидк", "ambulances"),
    ("генератор", "backup_generators"),
    ("патрул", "patrol_cars"),
)


def _http_get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=15) as resp:  # fixed clarity host
        return cast("dict[str, Any]", json.loads(resp.read().decode("utf-8")))


class ClarityRegistryClient:
    def __init__(
        self,
        api_key: str | None = None,
        fetch: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        self._key = api_key or os.getenv("CLARITY_API_KEY")
        self._fetch = fetch or _http_get_json

    def _call(self, method: str, **params: str) -> dict[str, Any]:
        if not self._key:
            raise RuntimeError("CLARITY_API_KEY is not set; cannot query Clarity Project API.")
        query = urllib.parse.urlencode({"key": self._key, **params})
        return self._fetch(f"{_BASE}/{method}?{query}")

    def find_entities(self, query: str) -> list[dict[str, Any]]:
        """edr.info search for communal enterprises of a community (best-effort)."""
        data = self._call("edr.info", q=query)
        items = data.get("data") or data.get("items") or data.get("result") or []
        return items if isinstance(items, list) else [items]

    def entity_vehicles(self, code: str) -> list[dict[str, Any]]:
        """vehicles.list for a legal entity by EDRPOU code (best-effort)."""
        data = self._call("vehicles.list", code=code)
        items = data.get("data") or data.get("items") or data.get("result") or []
        return items if isinstance(items, list) else [items]


def vehicles_to_endowment(vehicles: list[dict[str, Any]]) -> dict[str, Decimal]:
    """Aggregate raw Clarity vehicle records into endowment resource counts.

    Best-effort: classifies each record by keyword in its text fields. Unknown
    vehicles fall back to a generic `utility_vehicles` bucket.
    """
    counts: dict[str, Decimal] = {}
    for record in vehicles:
        text = " ".join(str(v) for v in record.values()).lower()
        matched = None
        for keyword, resource in _VEHICLE_KEYWORDS:
            if keyword in text:
                matched = resource
                break
        key = matched or "utility_vehicles"
        counts[key] = counts.get(key, Decimal("0")) + Decimal("1")
    return counts
