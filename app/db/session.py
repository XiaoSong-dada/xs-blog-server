from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from urllib.parse import quote_plus

from app.core.config import (
    settings,
)  # 你现在的 settings = Settings() :contentReference[oaicite:1]{index=1}


def build_async_db_url() -> str:
    """
    优先使用 settings.DATABASE_URL；
    没有则用 POSTGRES_* 拼接。
    """
    if settings.DATABASE_URL:  # :contentReference[oaicite:2]{index=2}
        return settings.DATABASE_URL

    # 来自你的配置：POSTGRES_HOST/PORT/USER/PASSWORD/DB :contentReference[oaicite:3]{index=3}
    host = settings.POSTGRES_HOST
    port = settings.POSTGRES_PORT
    user = settings.POSTGRES_USER
    password = settings.POSTGRES_PASSWORD
    db = settings.POSTGRES_DB

    # password 可能包含特殊字符（@ : / 等），必须 URL 编码
    pwd = quote_plus(password) if password else ""

    return f"postgresql+asyncpg://{user}:{pwd}@{host}:{port}/{db}"


DATABASE_URL = build_async_db_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
