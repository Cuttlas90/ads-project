from fastapi.testclient import TestClient

from app.main import app
from app.settings import Settings


def test_health_endpoint_ok(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.health.get_settings",
        lambda: Settings(
            _env_file=None,
            TELEGRAM_ENABLED=False,
            TON_ENABLED=False,
        ),
    )

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checks"]["backend"]["ready"] is True
    assert payload["checks"]["workers"]["ready"] is True
    assert payload["checks"]["ton"]["ready"] is True
    assert payload["checks"]["telegram"]["ready"] is True


def test_health_endpoint_degraded_when_ton_config_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.health.get_settings",
        lambda: Settings(
            _env_file=None,
            TELEGRAM_ENABLED=False,
            TON_ENABLED=True,
            TON_HOT_WALLET_MNEMONIC="some mnemonic",
            TON_FEE_PERCENT=1,
            TONCONNECT_MANIFEST_URL="https://example.com/manifest.json",
            TONCENTER_API=None,
        ),
    )

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["checks"]["ton"]["ready"] is False
    assert "TONCENTER_API" in payload["checks"]["ton"]["missing"]
