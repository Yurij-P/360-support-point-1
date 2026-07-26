from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def test_get_communities_catalog_api() -> None:
    response = client.get("/communities/catalog")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_count" in data
    assert data["total_count"] >= 1
    item = data["items"][0]
    assert "official_code" in item
    assert "preparedness_score" in item
    assert "critical_infrastructure_count" in item


def test_get_community_passport_api_success() -> None:
    community_id = "a29d6fbd-02c3-4d43-a651-7efd6fbd02c3"
    response = client.get(f"/communities/{community_id}/passport")
    assert response.status_code == 200
    data = response.json()
    assert data["community_id"] == community_id
    assert data["name"] == "Березнегуватська селищна громада"
    assert "infrastructure_items" in data
    items = data["infrastructure_items"]
    assert len(items) >= 5
    categories = [i["category"] for i in items]
    assert "POULTRY_FARM" in categories
    assert "TRANSFORMER_SUBSTATION" in categories
    assert "GAS_PIPELINE" in categories


def test_get_community_passport_api_not_found() -> None:
    response = client.get("/communities/non_existent_community/passport")
    assert response.status_code == 404
