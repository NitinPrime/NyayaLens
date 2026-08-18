"""Follow-up chat grounded in case context and retrieved law."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CaseMessage, CaseRecord
from app.llm.base import LLMProvider
from app.services.legal_retriever import LegalRetriever
from nyayalens_schemas.enums import MessageRole, StatementType
from nyayalens_schemas.models import ChatMessage, Citation, LegalSource

CHAT_SYSTEM_PROMPT = """You are NyayaLens, an Indian legal information assistant.
Use ONLY the retrieved legal sources for legal claims.
Do not invent sections, cases, or URLs.
Distinguish FACT, INFERENCE, LAW, ANALYSIS, and RECOMMENDATION.
Use cautious language. Never declare guilt or certain victory.
If the retrieved sources are insufficient, say so.
Remind the user that this is not a substitute for a qualified advocate.
"""


class ChatService:
    def __init__(self, db: AsyncSession, llm: LLMProvider, retriever: LegalRetriever):
        self.db = db
        self.llm = llm
        self.retriever = retriever

    async def list_messages(self, case_id: UUID) -> list[ChatMessage]:
        result = await self.db.execute(
            select(CaseMessage)
            .where(CaseMessage.case_id == case_id)
            .order_by(CaseMessage.created_at.asc())
        )
        rows = list(result.scalars().all())
        return [
            ChatMessage(
                id=row.id,
                case_id=row.case_id,
                role=MessageRole(row.role),
                content=row.content,
                citations=[Citation.model_validate(c) for c in (row.citations or [])],
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def ask(self, case: CaseRecord, question: str) -> tuple[ChatMessage, list[LegalSource]]:
        user_row = CaseMessage(case_id=case.id, role=MessageRole.USER.value, content=question)
        self.db.add(user_row)
        await self.db.flush()

        retrieved = await self.retriever.search(
            query=f"{question} {case.description}",
            issues=[case.case_type or ""],
            limit=4,
        )
        sources = [r.source for r in retrieved]
        source_block = "\n\n".join(
            f"[{s.title} — {s.section or 'N/A'}]\n{s.text}\nSource: {s.source_url or 'knowledge base'}"
            for s in sources
        ) or "No sufficiently relevant source was retrieved."

        history = await self.list_messages(case.id)
        history_text = "\n".join(f"{m.role.value}: {m.content}" for m in history[-8:])

        prompt = f"""CASE DESCRIPTION:
{case.description}

CASE TYPE: {case.case_type or "unknown"}

RETRIEVED LEGAL SOURCES:
{source_block}

RECENT CONVERSATION:
{history_text}

USER QUESTION:
{question}

Answer using the retrieved sources only for legal claims. Structure the answer with FACT / LAW / ANALYSIS / RECOMMENDATION labels where useful."""

        answer = await self.llm.generate(prompt, CHAT_SYSTEM_PROMPT)
        citations = [
            Citation(
                legal_source_id=s.id,
                claim=f"Potentially relevant: {s.title} {s.section or ''}".strip(),
                quoted_text=s.text[:280],
                is_verified=True,
                verification_note="Retrieved from the local legal knowledge base.",
                statement_type=StatementType.LEGAL_SOURCE,
            ).model_dump(mode="json")
            for s in sources
        ]

        assistant_row = CaseMessage(
            case_id=case.id,
            role=MessageRole.ASSISTANT.value,
            content=answer,
            citations=citations,
        )
        self.db.add(assistant_row)
        await self.db.flush()
        await self.db.refresh(assistant_row)

        message = ChatMessage(
            id=assistant_row.id,
            case_id=case.id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citations=[Citation.model_validate(c) for c in citations],
            created_at=assistant_row.created_at,
        )
        return message, sources
