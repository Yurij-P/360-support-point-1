from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def test_web_app_root_serving_index_html() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TPS360" in response.text
    # Mandatory NGO Anti-Corruption attribution check
    assert "ГО «Проти Корупції»" in response.text
    # Required navigation button IDs check
    assert "navCatalogBtn" in response.text
    assert "navScenariosBtn" in response.text
    assert "navWorkspaceBtn" in response.text
    assert "navFacilitatorBtn" in response.text
    assert "navAarBtn" in response.text


def test_web_app_static_css_and_js_serving() -> None:
    css_res = client.get("/static/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers["content-type"]

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers["content-type"]


def test_community_passport_gis_coordinates_and_katottg_alignment() -> None:
    res = client.get("/communities/catalog")
    assert res.status_code == 200
    catalog = res.json()
    assert "items" in catalog
    items = catalog["items"]
    assert len(items) >= 3

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


def test_specific_katottg_community_map_center_verification() -> None:
    """Explicitly verify KATOTTG codes and distinct GPS coordinates per community."""
    passports = {
        "verkhovyna": (48.155, 24.832, "UA26020010000055743", "Верховинська селищна громада"),
        "a29d6fbd-02c3-4d43-a651-7efd6fbd02c3": (47.312, 32.848, "UA48060030000037887", "Березнегуватська селищна громада"),
        "shiroke": (47.920, 35.050, "UA23080270000095874", "Широківська сільська громада"),
    }

    for comm_id, (expected_lat, expected_lon, expected_code, expected_name) in passports.items():
        res = client.get(f"/communities/{comm_id}/passport")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == expected_name
        assert data["official_code"] == expected_code
        assert abs(data["center_latitude"] - expected_lat) < 0.001
        assert abs(data["center_longitude"] - expected_lon) < 0.001
