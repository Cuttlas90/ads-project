from __future__ import annotations

import importlib.util
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from shared.db import session as db_session
from shared.db.base import SQLModel


def _load_alembic_env():
    env_path = Path(__file__).resolve().parents[2] / "backend" / "alembic" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load Alembic env module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_db_closes_session(monkeypatch) -> None:
    class TrackingSession(Session):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.closed_flag = False

        def close(self) -> None:  # type: ignore[override]
            self.closed_flag = True
            super().close()

    tracking_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_session.engine,
        class_=TrackingSession,
    )
    monkeypatch.setattr(db_session, "SessionLocal", tracking_factory)

    session_generator = db_session.get_db()
    db = next(session_generator)

    db.exec(text("SELECT 1"))

    session_generator.close()

    assert db.closed_flag is True


def test_alembic_target_metadata_includes_users() -> None:
    alembic_env = _load_alembic_env()

    assert alembic_env.target_metadata is SQLModel.metadata
    assert "users" in alembic_env.target_metadata.tables
