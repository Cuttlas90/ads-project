from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

ROOT_PATH = Path(__file__).resolve().parents[2]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from shared.db.base import SQLModel
from shared.db.session import get_database_url


target_metadata = SQLModel.metadata


def _configure_logging() -> None:
    config = context.config
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    _configure_logging()
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _configure_logging()
    config = context.config
    config.set_main_option("sqlalchemy.url", get_database_url())
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


def _try_run_migrations() -> None:
    try:
        config = context.config
    except Exception:
        return
    if config is None:
        return
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


_try_run_migrations()
