import logging

from app.logging import configure_logging
from app.settings import Settings


def test_logging_configuration(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    settings = Settings(_env_file=None)

    configure_logging(settings, force=True)

    assert logging.getLogger().level == logging.DEBUG
