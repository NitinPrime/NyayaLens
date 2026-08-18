"""Core Pydantic domain models for NyayaLens."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from nyayalens_schemas.enums import (
    AnalysisStatus,
    ConfidenceLevel,
    EvidenceType,
    FactType,
    IssuePriority,
    Jurisdiction,
    LegalDomain,
    LegalSourceType,
    MessageRole,
    PartyRole,
    RecommendationPriority,
    StatementType,
)


class Party(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    role: PartyRole = PartyRole.UNKNOWN
    description: Optional[str] = None


class Fact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    description: str
    fact_type: FactType = FactType.ALLEGED
    date: Optional[date] = None
    location: Optional[str] = None
    amount: Optional[str] = None
    source_evidence_ids: list[UUID] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_rationale: Optional[str] = None


class EvidencePassage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    text: str
    page_number: Optional[int] = None
    section_reference: Optional[str] = None
    supports_fact_ids: list[UUID] = Field(default_factory=list)
    contradicts_fact_ids: list[UUID] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class Evidence(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    evidence_type: EvidenceType
    mime_type: Optional[str] = None
    extracted_text: Optional[str] = None
    passages: list[EvidencePassage] = Field(default_factory=list)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


class Issue(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    issue: str
    why_it_matters: str
    supporting_fact_ids: list[UUID] = Field(default_factory=list)
    missing_fact_descriptions: list[str] = Field(default_factory=list)
    priority: IssuePriority = IssuePriority.MEDIUM


class LegalSource(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    source_type: LegalSourceType
    jurisdiction: Jurisdiction = Jurisdiction.INDIA
    section: Optional[str] = None
    article: Optional[str] = None
    text: str
    effective_date: Optional[date] = None
    repeal_date: Optional[date] = None
    source_url: Optional[str] = None
    version: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    legal_source_id: UUID
    claim: str
    quoted_text: Optional[str] = None
    is_verified: bool = False
    verification_note: Optional[str] = None
    statement_type: StatementType = StatementType.LEGAL_SOURCE


class LegalProvision(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    legal_source: LegalSource
    explanation: str
    applicability: str
    supporting_fact_ids: list[UUID] = Field(default_factory=list)
    missing_fact_descriptions: list[str] = Field(default_factory=list)
    uncertainty: str
    counterarguments: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    citations: list[Citation] = Field(default_factory=list)


class Argument(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    position: str
    strongest_arguments: list[str] = Field(default_factory=list)
    supporting_fact_ids: list[UUID] = Field(default_factory=list)
    supporting_source_ids: list[UUID] = Field(default_factory=list)
    possible_defenses: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class MissingInformation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    question: str
    why_it_matters: str
    priority: IssuePriority = IssuePriority.MEDIUM
    related_issue_ids: list[UUID] = Field(default_factory=list)


class Recommendation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    action: str
    rationale: str
    priority: RecommendationPriority = RecommendationPriority.MEDIUM


class LegalAnalysis(BaseModel):
    issue_id: UUID
    provisions: list[LegalProvision] = Field(default_factory=list)
    summary: str
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class ChatMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    role: MessageRole
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=8000)


class ChatResponse(BaseModel):
    message: ChatMessage
    retrieved_sources: list[LegalSource] = Field(default_factory=list)


class Analysis(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    status: AnalysisStatus = AnalysisStatus.PENDING
    summary: Optional[str] = None
    legal_domains: list[LegalDomain] = Field(default_factory=list)
    inferred_facts: list[str] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    legal_analyses: list[LegalAnalysis] = Field(default_factory=list)
    claimant_argument: Optional[Argument] = None
    respondent_argument: Optional[Argument] = None
    missing_information: list[MissingInformation] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    retrieved_sources: list[LegalSource] = Field(default_factory=list)
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    uncertainty_explanation: Optional[str] = None
    unsupported_claims: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "NyayaLens provides general legal information and AI-assisted case analysis. "
        "It is not a substitute for advice from a qualified advocate. "
        "Legal outcomes depend on facts, evidence, jurisdiction, procedure, and applicable law."
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class Case(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: Optional[str] = None
    description: str
    case_type: Optional[str] = None
    incident_date: Optional[date] = None
    location: Optional[str] = None
    jurisdiction: Jurisdiction = Jurisdiction.INDIA
    is_demo: bool = False
    parties: list[Party] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CaseCreate(BaseModel):
    description: str = Field(..., min_length=10, max_length=50000)
    title: Optional[str] = Field(None, max_length=500)
    incident_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=500)
    amount: Optional[str] = Field(None, max_length=100)
    parties_involved: Optional[str] = Field(None, max_length=2000)
    evidence_available: Optional[str] = Field(None, max_length=5000)
    additional_context: Optional[str] = Field(None, max_length=10000)
    jurisdiction: Jurisdiction = Jurisdiction.INDIA
    case_type: Optional[str] = Field(None, max_length=200)
    is_demo: bool = False


class CaseSummary(BaseModel):
    id: UUID
    title: Optional[str] = None
    case_type: Optional[str] = None
    description_preview: str
    party_count: int = 0
    fact_count: int = 0
    created_at: datetime
    has_analysis: bool = False
