from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def load_local_env() -> None:
    """Load env vars from local env files if they are not set in process env."""
    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / "compose" / ".local.env",
        root / "local.env",
        root / ".local.env",
    ]

    for env_file in candidates:
        if not env_file.exists():
            continue

        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)

        break


def build_sync_database_url() -> str:
    load_local_env()

    from app.core.config import settings

    if settings.DATABASE_URL:
        db_url = settings.DATABASE_URL
    else:
        user = settings.POSTGRES_USER
        password = quote_plus(settings.POSTGRES_PASSWORD or "")
        host = settings.POSTGRES_HOST
        port = settings.POSTGRES_PORT
        database = settings.POSTGRES_DB
        db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"

    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return db_url


sync_database_url = build_sync_database_url()
config.set_main_option("sqlalchemy.url", sync_database_url.replace("%", "%%"))

from app.db.base import ORMBase
import app.models  # noqa: F401

target_metadata = ORMBase.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
