from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def test_get_scenarios_catalog_api() -> None:
    response = client.get("/scenarios/catalog")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_count" in data
    assert data["total_count"] >= 4
    scenario_ids = [item["id"] for item in data["items"]]
    assert "scen_flooding_v1" in scenario_ids
    assert "scen_epizootic_v1" in scenario_ids
    assert "scen_blackout_v1" in scenario_ids
    assert "scen_wartime_defense_v1" in scenario_ids


def test_check_scenario_compatibility_api_success() -> None:
    community_id = "a29d6fbd-02c3-4d43-a651-7efd6fbd02c3"
    scenario_id = "scen_flooding_v1"

    payload = {"scenario_id": scenario_id, "community_id": community_id}
    response = client.post("/scenarios/compatibility-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == scenario_id
    assert data["community_id"] == community_id
    assert "is_compatible" in data
    assert "match_score" in data


def test_check_scenario_compatibility_api_not_found() -> None:
    payload = {"scenario_id": "scen_flooding_v1", "community_id": "invalid_community"}
    response = client.post("/scenarios/compatibility-check", json=payload)
    assert response.status_code == 404


def test_get_simulation_context_snapshot_api() -> None:
    session_id = "sess_demo_1001"
    response = client.get(f"/simulations/{session_id}/context-snapshot")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "community_passport" in data
    assert "time_dilation_clock" in data
    assert data["is_osm_bounded"] is True
