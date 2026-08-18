"""Case follow-up chat."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import TokenUser, assert_case_access, get_current_user_optional
from app.config import get_settings
from app.db.session import get_db
from app.llm.base import get_llm_provider
from app.services.case_service import CaseService
from app.services.chat_service import ChatService
from app.services.legal_retriever import LegalRetriever
from nyayalens_schemas.models import ChatMessage, ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


def _chat_service(db: AsyncSession) -> ChatService:
    settings = get_settings()
    llm = get_llm_provider(
        settings.llm_provider,
        api_key=settings.openai_api_key or settings.anthropic_api_key,
        model=settings.llm_model,
    )
    return ChatService(db, llm, LegalRetriever(db, llm))


@router.get("/cases/{case_id}/messages", response_model=list[ChatMessage])
async def list_messages(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenUser | None = Depends(get_current_user_optional),
) -> list[ChatMessage]:
    case = await CaseService(db).get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    await assert_case_access(case, user)
    return await _chat_service(db).list_messages(case_id)


@router.post("/cases/{case_id}/messages", response_model=ChatResponse)
async def post_message(
    case_id: UUID,
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenUser | None = Depends(get_current_user_optional),
) -> ChatResponse:
    case = await CaseService(db).get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    await assert_case_access(case, user)
    message, sources = await _chat_service(db).ask(case, data.message)
    return ChatResponse(message=message, retrieved_sources=sources)
