"""Case business logic service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AnalysisRecord, CaseRecord
from nyayalens_schemas.enums import AnalysisStatus
from nyayalens_schemas.models import Case, CaseCreate, CaseSummary, Party, Fact
from nyayalens_schemas.enums import FactType, PartyRole, ConfidenceLevel


class CaseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_case(self, data: CaseCreate, user_id: UUID | None = None) -> CaseRecord:
        extras = {
            "amount": data.amount,
            "parties_involved": data.parties_involved,
            "evidence_available": data.evidence_available,
            "additional_context": data.additional_context,
        }
        description = data.description.strip()
        if data.parties_involved:
            description += f"\n\nParties involved: {data.parties_involved}"
        if data.amount:
            description += f"\nAmount involved: {data.amount}"
        if data.evidence_available:
            description += f"\nEvidence available: {data.evidence_available}"
        if data.additional_context:
            description += f"\nAdditional context: {data.additional_context}"

        case = CaseRecord(
            description=description,
            title=data.title,
            incident_date=data.incident_date,
            location=data.location,
            amount=data.amount,
            jurisdiction=data.jurisdiction,
            case_type=data.case_type,
            is_demo=data.is_demo,
            user_id=user_id,
            structured_data={k: v for k, v in extras.items() if v},
        )
        self.db.add(case)
        await self.db.flush()
        return case

    async def get_case(self, case_id: UUID) -> CaseRecord | None:
        result = await self.db.execute(
            select(CaseRecord)
            .options(
                selectinload(CaseRecord.parties),
                selectinload(CaseRecord.facts),
                selectinload(CaseRecord.evidence_items),
                selectinload(CaseRecord.analyses),
            )
            .where(CaseRecord.id == case_id)
        )
        return result.scalar_one_or_none()

    async def list_cases(
        self, limit: int = 50, offset: int = 0, user_id: UUID | None = None
    ) -> list[CaseRecord]:
        query = (
            select(CaseRecord)
            .options(
                selectinload(CaseRecord.parties),
                selectinload(CaseRecord.facts),
                selectinload(CaseRecord.analyses),
            )
            .order_by(CaseRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if user_id:
            query = query.where((CaseRecord.user_id == user_id) | (CaseRecord.is_demo.is_(True)))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def to_domain(self, record: CaseRecord) -> Case:
        return Case(
            id=record.id,
            title=record.title,
            description=record.description,
            case_type=record.case_type,
            incident_date=record.incident_date,
            location=record.location,
            jurisdiction=record.jurisdiction,
            is_demo=record.is_demo,
            parties=[
                Party(
                    id=p.id,
                    name=p.name,
                    role=PartyRole(p.role),
                    description=p.description,
                )
                for p in record.parties
            ],
            facts=[
                Fact(
                    id=f.id,
                    description=f.description,
                    fact_type=FactType(f.fact_type),
                    date=f.fact_date,
                    location=f.location,
                    amount=f.amount,
                    confidence=ConfidenceLevel(f.confidence) if f.confidence else ConfidenceLevel.MEDIUM,
                    confidence_rationale=f.confidence_rationale,
                    source_evidence_ids=f.source_evidence_ids or [],
                )
                for f in record.facts
            ],
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def to_summary(self, record: CaseRecord) -> CaseSummary:
        has_analysis = any(a.status == AnalysisStatus.COMPLETED for a in record.analyses) if record.analyses else False
        preview = record.description[:200] + ("..." if len(record.description) > 200 else "")
        return CaseSummary(
            id=record.id,
            title=record.title,
            case_type=record.case_type,
            description_preview=preview,
            party_count=len(record.parties),
            fact_count=len(record.facts),
            created_at=record.created_at,
            has_analysis=has_analysis,
        )
