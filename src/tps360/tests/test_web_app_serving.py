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
