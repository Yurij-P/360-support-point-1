from decimal import Decimal

import pytest

from tps360.simulation.services.registry_clarity import (
    ClarityRegistryClient,
    vehicles_to_endowment,
)


def test_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLARITY_API_KEY", raising=False)
    client = ClarityRegistryClient(fetch=lambda url: {"data": []})
    with pytest.raises(RuntimeError):
        client.search_entities("КП Водоканал")


def test_search_entities_uses_edr_search_and_key() -> None:
    seen: dict[str, str] = {}

    def fetch(url: str) -> dict[str, object]:
        seen["url"] = url
        return {"data": [{"code": "12345678", "name": "КП Водоканал"}], "quota": {}}

    client = ClarityRegistryClient(api_key="test-key", fetch=fetch)
    items = client.search_entities("Водоканал")
    assert items[0]["code"] == "12345678"
    assert "edr.search" in seen["url"]
    assert "key=test-key" in seen["url"]


def test_entity_vehicles_uses_path_based_method() -> None:
    seen: dict[str, str] = {}

    def fetch(url: str) -> dict[str, object]:
        seen["url"] = url
        return {"data": [{"model": "Трактор МТЗ-82"}]}

    client = ClarityRegistryClient(api_key="k", fetch=fetch)
    vehicles = client.entity_vehicles("12345678")
    assert len(vehicles) == 1
    assert "vehicles.list/12345678" in seen["url"]


def test_api_error_raises() -> None:
    client = ClarityRegistryClient(api_key="k", fetch=lambda url: {"error": {"code": 401}})
    with pytest.raises(RuntimeError):
        client.entity_info("12345678")


def test_vehicles_to_endowment_classifies() -> None:
    vehicles = [
        {"model": "Трактор МТЗ-82"},
        {"type": "Асенізатор КО-503"},
        {"model": "Автоцистерна пожежна"},
        {"model": "Невідома вантажівка"},
    ]
    res = vehicles_to_endowment(vehicles)
    assert res["tractors"] == Decimal("1")
    assert res["sewage_trucks"] == Decimal("1")
    assert res["water_tankers"] == Decimal("1")
    assert res["utility_vehicles"] == Decimal("1")  # unknown fallback
