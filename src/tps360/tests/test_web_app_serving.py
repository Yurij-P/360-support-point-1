from fastapi.testclient import TestClient

from tps360.api.main import app

client = TestClient(app)


def test_web_app_root_serving_index_html() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TPS360" in response.text


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
