"""Hybrid legal source retrieval — keyword + embedding similarity."""

import math
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LegalSourceRecord
from app.llm.base import LLMProvider
from nyayalens_schemas.models import LegalSource


@dataclass
class RetrievalResult:
    source: LegalSource
    keyword_score: float
    vector_score: float
    combined_score: float


STOPWORDS = {
    "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "is", "are", "was", "were",
    "be", "by", "with", "from", "that", "this", "it", "as", "at", "if", "not", "no", "my",
    "i", "he", "she", "they", "we", "you", "his", "her", "their", "any", "may", "shall",
}


def _tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def _keyword_score(query_tokens: set[str], record: LegalSourceRecord) -> float:
    topics = " ".join(record.amendment_history or [])
    corpus = f"{record.title} {record.section or ''} {record.text} {topics}".lower()
    doc_tokens = _tokenize(corpus)
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & doc_tokens)
    return overlap / len(query_tokens)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _to_domain(record: LegalSourceRecord) -> LegalSource:
    return LegalSource(
        id=record.id,
        title=record.title,
        source_type=record.source_type,
        jurisdiction=record.jurisdiction,
        section=record.section,
        text=record.text,
        effective_date=record.effective_date,
        repeal_date=record.repeal_date,
        source_url=record.source_url,
        version=record.version,
    )


class LegalRetriever:
    """Hybrid retrieval over seeded legal sources."""

    def __init__(self, db: AsyncSession, llm: LLMProvider):
        self.db = db
        self.llm = llm

    async def search(
        self,
        query: str,
        issues: list[str] | None = None,
        limit: int = 5,
        min_score: float = 0.12,
    ) -> list[RetrievalResult]:
        result = await self.db.execute(select(LegalSourceRecord))
        records = list(result.scalars().all())
        if not records:
            return []

        search_text = query
        if issues:
            search_text += " " + " ".join(issues)

        query_tokens = _tokenize(search_text)
        query_embedding = (await self.llm.embed([search_text]))[0]

        scored: list[RetrievalResult] = []
        for record in records:
            kw = _keyword_score(query_tokens, record)
            vec = 0.0
            if record.embedding and query_embedding:
                vec = _cosine_similarity(query_embedding, record.embedding)
            combined = (0.75 * kw) + (0.25 * vec)
            if kw >= 0.1 and combined >= min_score:
                scored.append(
                    RetrievalResult(
                        source=_to_domain(record),
                        keyword_score=kw,
                        vector_score=vec,
                        combined_score=combined,
                    )
                )

        scored.sort(key=lambda r: r.combined_score, reverse=True)
        return scored[:limit]
