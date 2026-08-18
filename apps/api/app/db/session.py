"""Database session management."""

import logging
from collections.abc import AsyncGenerator
from urllib.parse import urlsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db.url import postgres_connect_args

logger = logging.getLogger(__name__)
settings = get_settings()

engine_kwargs: dict = {"echo": False}

if settings.is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs["pool_pre_ping"] = True
    connect_args = postgres_connect_args(settings.database_url)
    if connect_args:
        engine_kwargs["connect_args"] = connect_args
    host = urlsplit(settings.database_url.replace("postgresql+asyncpg://", "https://")).hostname
    logger.info("Using Postgres host %s", host)

engine = create_async_engine(settings.database_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
