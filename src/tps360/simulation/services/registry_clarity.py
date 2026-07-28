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
import urllib.error
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

    def _call(self, path: str, **params: str) -> dict[str, Any]:
        """Path-based Clarity call, e.g. `edr.info/14360570` or `edr.search`."""
        if not self._key:
            raise RuntimeError("CLARITY_API_KEY is not set; cannot query Clarity Project API.")
        query = urllib.parse.urlencode({"key": self._key, **params})
        try:
            data = self._fetch(f"{_BASE}/{path}?{query}")
        except urllib.error.HTTPError as exc:
            # e.g. 402 Payment Required (unfunded key), 403, 5xx.
            raise RuntimeError(f"Clarity API HTTP {exc.code}: {exc.reason}") from exc
        if isinstance(data, dict):
            if data.get("error"):
                raise RuntimeError(f"Clarity API error: {data['error']}")
            # Errors also arrive top-level, e.g. {"code": 403, "text": "This key is inactive"}.
            code = data.get("code")
            if isinstance(code, int) and code >= 400:
                raise RuntimeError(f"Clarity API error {code}: {data.get('text', '')}")
        return data

    @staticmethod
    def _items(data: dict[str, Any]) -> list[dict[str, Any]]:
        items = data.get("data") or data.get("items") or data.get("result") or []
        return items if isinstance(items, list) else [items]

    def search_entities(self, query: str) -> list[dict[str, Any]]:
        """edr.search — find communal enterprises of a community (best-effort)."""
        return self._items(self._call("edr.search", q=query))

    def entity_info(self, edrpou: str) -> dict[str, Any]:
        """edr.info/{edrpou} — legal entity by EDRPOU/RNOKPP code."""
        return self._call(f"edr.info/{urllib.parse.quote(edrpou)}")

    def entity_vehicles(self, edrpou: str) -> list[dict[str, Any]]:
        """vehicles.list/{code} — vehicles owned by a legal entity (real fleet)."""
        return self._items(self._call(f"vehicles.list/{urllib.parse.quote(edrpou)}"))


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
