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
    # Pick a real community from the KATOTTG catalog rather than hardcoding one.
    catalog = client.get("/communities/catalog").json()
    item = catalog["items"][0]
    community_id = item["community_id"]

    response = client.get(f"/communities/{community_id}/passport")
    assert response.status_code == 200
    data = response.json()
    assert data["community_id"] == community_id
    assert data["name"] == item["name"]
    assert "infrastructure_items" in data
    items = data["infrastructure_items"]
    # Every community gets the canonical KATOTTG-derived infrastructure baseline.
    assert len(items) >= 4
    categories = [i["category"] for i in items]
    assert "TERRITORIAL_DEFENSE_HQ" in categories
    assert "RESCUE_FIRE_STATION" in categories
    assert "HOSPITAL_MEDICAL" in categories
    assert "TRANSFORMER_SUBSTATION" in categories


def test_get_community_passport_api_not_found() -> None:
    response = client.get("/communities/non_existent_community/passport")
    assert response.status_code == 404
