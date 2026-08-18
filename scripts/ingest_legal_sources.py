"""Idempotent legal-source ingestion from data/legal_sources/seed_sources.json."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "schemas"))

from app.db.init_db import init_db  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.llm.base import get_llm_provider  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.services.legal_ingestion import seed_legal_sources  # noqa: E402


async def main() -> None:
    await init_db(engine)
    settings = get_settings()
    llm = get_llm_provider(
        settings.llm_provider,
        api_key=settings.openai_api_key or settings.anthropic_api_key,
        model=settings.llm_model,
    )
    async with AsyncSessionLocal() as session:
        count = await seed_legal_sources(session, llm=llm)
        await session.commit()
    print(f"Ingested {count} new legal sources.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
