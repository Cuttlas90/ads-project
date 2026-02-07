from fastapi.testclient import TestClient

from app.main import app


def test_preflight_allows_configured_origin() -> None:
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_preflight_allows_app_domain_origin() -> None:
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "https://app.chainofwinners.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.chainofwinners.com"
