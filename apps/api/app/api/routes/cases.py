"""API route handlers."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import TokenUser, assert_case_access, get_current_user_optional
from app.db.session import get_db
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.case_service import CaseService
from nyayalens_schemas.models import Analysis, Case, CaseCreate, CaseSummary, LegalSource

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=Case, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    user: Optional[TokenUser] = Depends(get_current_user_optional),
) -> Case:
    service = CaseService(db)
    record = await service.create_case(data, user_id=user.id if user else None)
    await db.refresh(record, ["parties", "facts"])
    return service.to_domain(record)


@router.get("", response_model=list[CaseSummary])
async def list_cases(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: Optional[TokenUser] = Depends(get_current_user_optional),
) -> list[CaseSummary]:
    service = CaseService(db)
    user_id = user.id if user else None
    records = await service.list_cases(limit=limit, offset=offset, user_id=user_id)
    return [service.to_summary(r) for r in records]


@router.get("/{case_id}", response_model=Case)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: Optional[TokenUser] = Depends(get_current_user_optional),
) -> Case:
    service = CaseService(db)
    record = await service.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found")
    await assert_case_access(record, user)
    return service.to_domain(record)


@router.post("/{case_id}/analyze", response_model=Analysis, status_code=status.HTTP_202_ACCEPTED)
async def analyze_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: Optional[TokenUser] = Depends(get_current_user_optional),
) -> Analysis:
    service = CaseService(db)
    record = await service.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found")
    await assert_case_access(record, user)

    orchestrator = AnalysisOrchestrator(db)
    analysis_record = await orchestrator.run_analysis(record)
    return Analysis.model_validate(analysis_record.result)


@router.get("/{case_id}/analysis", response_model=Analysis)
async def get_analysis(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: Optional[TokenUser] = Depends(get_current_user_optional),
) -> Analysis:
    service = CaseService(db)
    record = await service.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found")
    await assert_case_access(record, user)

    completed = [a for a in record.analyses if a.status.value == "completed"]
    if not completed:
        raise HTTPException(status_code=404, detail="No completed analysis found for this case")

    latest = sorted(completed, key=lambda a: a.created_at, reverse=True)[0]
    return Analysis.model_validate(latest.result)


@router.get("/{case_id}/sources", response_model=list[LegalSource])
async def get_case_sources(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: Optional[TokenUser] = Depends(get_current_user_optional),
) -> list[LegalSource]:
    service = CaseService(db)
    record = await service.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found")
    await assert_case_access(record, user)
    completed = [a for a in record.analyses if a.status.value == "completed"]
    if not completed:
        return []
    latest = sorted(completed, key=lambda a: a.created_at, reverse=True)[0]
    analysis = Analysis.model_validate(latest.result)
    return analysis.retrieved_sources
