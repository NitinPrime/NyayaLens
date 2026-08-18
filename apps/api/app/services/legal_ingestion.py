"""Load authoritative legal sources into the database."""

import json
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import REPO_ROOT
from app.db.models import LegalChunk, LegalSourceRecord
from nyayalens_schemas.enums import Jurisdiction, LegalSourceType

logger = logging.getLogger(__name__)

SEED_FILE = REPO_ROOT / "data" / "legal_sources" / "seed_sources.json"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def chunk_text(text: str, size: int = 600) -> list[str]:
    text = " ".join(text.split())
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += size - 80
    return chunks


async def seed_legal_sources(db: AsyncSession, llm=None) -> int:
    """Idempotent seed from JSON. Inserts only missing title+section pairs."""
    if not SEED_FILE.exists():
        logger.warning("Seed file not found: %s", SEED_FILE)
        return 0

    with open(SEED_FILE, encoding="utf-8") as f:
        sources = json.load(f)

    existing = await db.execute(select(LegalSourceRecord.title, LegalSourceRecord.section))
    existing_keys = {(row[0], row[1]) for row in existing.all()}

    to_insert = [s for s in sources if (s["title"], s.get("section")) not in existing_keys]
    if not to_insert:
        logger.info("Legal sources already up to date (%d records)", len(existing_keys))
        return 0

    embeddings: list[list[float]] = []
    if llm:
        texts = [
            f"{s['title']} {s.get('section', '')} {s['text']} {' '.join(s.get('topics', []))}"
            for s in to_insert
        ]
        embeddings = await llm.embed(texts)

    inserted = 0
    for idx, source in enumerate(to_insert):
        record = LegalSourceRecord(
            title=source["title"],
            source_type=LegalSourceType(source["source_type"]),
            jurisdiction=Jurisdiction.INDIA,
            section=source.get("section"),
            text=source["text"],
            effective_date=_parse_date(source.get("effective_date")),
            source_url=source.get("source_url"),
            version="seed-v1",
            amendment_history=source.get("topics", []),
            embedding=embeddings[idx] if embeddings else None,
        )
        db.add(record)
        await db.flush()
        for i, part in enumerate(chunk_text(source["text"])):
            db.add(
                LegalChunk(
                    source_id=record.id,
                    text=part,
                    chunk_index=i,
                    embedding=embeddings[idx] if embeddings else None,
                )
            )
        inserted += 1

    await db.flush()
    logger.info("Seeded %d new legal sources", inserted)
    return inserted
