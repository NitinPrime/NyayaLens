"""Structured output for legal analysis — Stage 4."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from nyayalens_schemas.enums import ConfidenceLevel


class AnalyzedProvision(BaseModel):
    legal_source_id: UUID
    explanation: str
    applicability: str
    uncertainty: str
    counterarguments: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    claim: str


class IssueLegalAnalysis(BaseModel):
    issue_id: UUID
    summary: str
    provisions: list[AnalyzedProvision] = Field(default_factory=list)
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class LegalAnalysisResult(BaseModel):
    analyses: list[IssueLegalAnalysis] = Field(default_factory=list)
