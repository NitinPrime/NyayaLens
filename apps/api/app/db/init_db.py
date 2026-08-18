"""Database initialization."""

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import DATA_DIR, get_settings
from app.db.models import Base
from app.db.session import AsyncSessionLocal
from app.llm.base import get_llm_provider
from app.services.legal_ingestion import seed_legal_sources


async def init_db(engine: AsyncEngine) -> None:
    settings = get_settings()
    if settings.is_sqlite:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.is_sqlite:
            try:
                await conn.execute(text("ALTER TABLE cases ADD COLUMN amount VARCHAR(100)"))
            except Exception:
                pass

    llm = get_llm_provider(
        settings.llm_provider,
        api_key=settings.openai_api_key or settings.anthropic_api_key,
        model=settings.llm_model,
    )
    async with AsyncSessionLocal() as session:
        await seed_legal_sources(session, llm=llm)
        await session.commit()
