"""data.gov.ua (CKAN) adapter — FREE, keyless source of real communal enterprises.

Unlike Clarity Project (paid, HTTP 402), the national open-data portal exposes a
keyless CKAN API. Best-effort: a community must have published a КП dataset, and
column names vary, so extraction is tolerant.

CKAN: {base}/package_search?q=... then {base}/datastore_search?resource_id=...
HTTP is injectable so tests never hit the network.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any, cast

_BASE = "https://data.gov.ua/api/3/action"

_NAME_FIELDS = ("Назва підприємства", "Повна назва", "name", "Назва")
_EDRPOU_FIELDS = ("Код ЄДРПОУ", "ЄДРПОУ", "edrpou", "Код")


def _http_get_json(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return cast("dict[str, Any]", json.loads(resp.read().decode("utf-8")))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"data.gov.ua HTTP {exc.code}: {exc.reason}") from exc


def _first(record: dict[str, Any], fields: tuple[str, ...]) -> str | None:
    for field in fields:
        value = record.get(field)
        if value:
            return str(value)
    return None


class DataGovUaClient:
    def __init__(self, fetch: Callable[[str], dict[str, Any]] | None = None) -> None:
        self._fetch = fetch or _http_get_json

    def _call(self, action: str, **params: str) -> dict[str, Any]:
        query = urllib.parse.urlencode(params)
        return self._fetch(f"{_BASE}/{action}?{query}")

    def search_communal_enterprises(self, hromada_name: str) -> list[dict[str, Any]]:
        """Find communal enterprises of a hromada via CKAN (best-effort, keyless)."""
        search = self._call("package_search", q=f"комунальні підприємства {hromada_name}")
        results = search.get("result", {}).get("results", [])
        if not results:
            return []

        resource_id: str | None = None
        for resource in results[0].get("resources", []):
            if str(resource.get("format", "")).upper() in ("CSV", "JSON"):
                resource_id = resource.get("id")
                break
        if not resource_id:
            return []

        store = self._call("datastore_search", resource_id=resource_id, limit="100")
        records = store.get("result", {}).get("records", [])
        return [self._normalize(rec) for rec in records]

    @staticmethod
    def _normalize(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": _first(record, _NAME_FIELDS),
            "edrpou": _first(record, _EDRPOU_FIELDS),
            "raw": record,
        }
