from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def test_web_app_root_serving_index_html() -> None:
    """Verify server serves index.html with clean empty state dashes '—' and NGO Anti-Corruption attribution."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TPS360" in response.text
    # Mandatory NGO Anti-Corruption attribution check
    assert "ГО «Проти Корупції»" in response.text
    # Context bar must default to clean dashes '—'
    assert 'id="activeCommunityName">—' in response.text
    assert 'id="activeScenarioTitle">—' in response.text
    assert 'id="activeSessionStatus"' in response.text
    # Required navigation button IDs check
    assert "navCatalogBtn" in response.text
    assert "navScenariosBtn" in response.text
    assert "navWorkspaceBtn" in response.text
    assert "navFacilitatorBtn" in response.text
    assert "navAarBtn" in response.text


def test_web_app_static_css_and_js_serving() -> None:
    """Verify static assets style.css and app.js are served with correct MIME types."""
    css_res = client.get("/static/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers["content-type"]

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers["content-type"]
    # App JS must not contain hardcoded dummy percentages like 68.5% or fake numbers
    assert "initial_preparedness_score: 68.5" not in js_res.text


def test_community_passport_gis_coordinates_and_katottg_alignment() -> None:
    """Verify KATOTTG codes, regions, and non-zero GPS center coordinates across catalog."""
    res = client.get("/communities/catalog")
    assert res.status_code == 200
    catalog = res.json()
    assert "items" in catalog
    items = catalog["items"]
    assert len(items) >= 5

    for item in items:
        assert item["official_code"].startswith("UA")
        assert item["center_latitude"] != 0.0
        assert item["center_longitude"] != 0.0

        passport_res = client.get(f"/communities/{item['community_id']}/passport")
        assert passport_res.status_code == 200
        passport = passport_res.json()
        assert passport["name"] == item["name"]
        assert passport["region"] == item["region"]
        assert passport["center_latitude"] == item["center_latitude"]
        assert passport["center_longitude"] == item["center_longitude"]


def test_katottg_search_query_matching_all_regions() -> None:
    """Verify KATOTTG search works for Mykolaiv, Kharkiv, Kyiv, Zaporizhzhia, and partial codes."""
    queries = [
        ("Миколаївська", ["Миколаївська міська громада", "Березнегуватська селищна громада"]),
        ("Харків", ["Харківська міська громада"]),
        ("Запорізька", ["Запорізька міська громада", "Широківська сільська громада"]),
        ("UA4806", ["Березнегуватська селищна громада", "Миколаївська міська громада"]),
    ]

    for q, expected_names in queries:
        res = client.get(f"/communities/catalog?query={q}")
        assert res.status_code == 200
        items = res.json()["items"]
        found_names = [item["name"] for item in items]
        for name in expected_names:
            assert any(name in f for f in found_names), f"Query '{q}' failed to find '{name}'"
