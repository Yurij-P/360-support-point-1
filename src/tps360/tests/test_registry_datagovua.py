from typing import Any

from tps360.simulation.services.registry_datagovua import DataGovUaClient


def _fetch_two_step(url: str) -> dict[str, Any]:
    if "package_search" in url:
        return {
            "result": {
                "results": [
                    {"resources": [{"format": "CSV", "id": "res-1"}]}
                ]
            }
        }
    if "datastore_search" in url:
        return {
            "result": {
                "records": [
                    {"Назва підприємства": "КП Водоканал", "Код ЄДРПОУ": "12345678"},
                    {"name": "КП Благоустрій", "edrpou": "87654321"},
                ]
            }
        }
    return {}


def test_search_communal_enterprises_normalizes_records() -> None:
    client = DataGovUaClient(fetch=_fetch_two_step)
    items = client.search_communal_enterprises("Житомир")
    assert len(items) == 2
    assert items[0]["name"] == "КП Водоканал"
    assert items[0]["edrpou"] == "12345678"
    assert items[1]["name"] == "КП Благоустрій"  # alternate column names handled


def test_no_dataset_returns_empty() -> None:
    client = DataGovUaClient(fetch=lambda url: {"result": {"results": []}})
    assert client.search_communal_enterprises("Невідома") == []


def test_no_tabular_resource_returns_empty() -> None:
    def fetch(url: str) -> dict[str, Any]:
        return {"result": {"results": [{"resources": [{"format": "PDF", "id": "x"}]}]}}

    assert DataGovUaClient(fetch=fetch).search_communal_enterprises("Х") == []
