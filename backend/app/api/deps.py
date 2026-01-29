from app.settings import Settings, get_settings
from shared.db.session import get_db as shared_get_db


def get_settings_dep() -> Settings:
    return get_settings()


def get_db():
    yield from shared_get_db()
