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
        client.find_entities("КП Водоканал")


def test_find_entities_parses_and_passes_key() -> None:
    seen: dict[str, str] = {}

    def fetch(url: str) -> dict[str, object]:
        seen["url"] = url
        return {"data": [{"code": "12345678", "name": "КП Водоканал"}]}

    client = ClarityRegistryClient(api_key="test-key", fetch=fetch)
    items = client.find_entities("Водоканал")
    assert items[0]["code"] == "12345678"
    assert "key=test-key" in seen["url"]
    assert "edr.info" in seen["url"]


def test_entity_vehicles_uses_vehicles_list() -> None:
    seen: dict[str, str] = {}

    def fetch(url: str) -> dict[str, object]:
        seen["url"] = url
        return {"data": [{"model": "Трактор МТЗ-82"}]}

    client = ClarityRegistryClient(api_key="k", fetch=fetch)
    vehicles = client.entity_vehicles("12345678")
    assert len(vehicles) == 1
    assert "vehicles.list" in seen["url"]
    assert "code=12345678" in seen["url"]


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
