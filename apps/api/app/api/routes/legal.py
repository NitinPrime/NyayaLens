"""Legal knowledge-base search and admin listing."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LegalSourceRecord
from app.db.session import get_db
from app.llm.base import get_llm_provider
from app.config import get_settings
from app.services.legal_retriever import LegalRetriever
from nyayalens_schemas.models import LegalSource

router = APIRouter(prefix="/legal", tags=["legal"])


class LegalSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    limit: int = Field(default=8, ge=1, le=25)


@router.post("/search", response_model=list[LegalSource])
async def search_legal(data: LegalSearchRequest, db: AsyncSession = Depends(get_db)) -> list[LegalSource]:
    settings = get_settings()
    llm = get_llm_provider(
        settings.llm_provider,
        api_key=settings.openai_api_key or settings.anthropic_api_key,
        model=settings.llm_model,
    )
    retriever = LegalRetriever(db, llm)
    results = await retriever.search(query=data.query, limit=data.limit)
    return [r.source for r in results]


@router.get("/sources", response_model=list[LegalSource])
async def list_sources(db: AsyncSession = Depends(get_db)) -> list[LegalSource]:
    result = await db.execute(select(LegalSourceRecord).order_by(LegalSourceRecord.title, LegalSourceRecord.section))
    records = list(result.scalars().all())
    return [
        LegalSource(
            id=r.id,
            title=r.title,
            source_type=r.source_type,
            jurisdiction=r.jurisdiction,
            section=r.section,
            text=r.text,
            effective_date=r.effective_date,
            repeal_date=r.repeal_date,
            source_url=r.source_url,
            version=r.version,
        )
        for r in records
    ]
