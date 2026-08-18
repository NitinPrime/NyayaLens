"""Structured output for both-side argument analysis — Stage 5."""

from pydantic import BaseModel, Field

from nyayalens_schemas.enums import ConfidenceLevel


class SideAnalysis(BaseModel):
    position: str
    strongest_arguments: list[str] = Field(default_factory=list)
    possible_defenses: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class ArgumentAnalysisResult(BaseModel):
    claimant: SideAnalysis
    respondent: SideAnalysis
