"""Structured output for issue identification — Stage 2."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from nyayalens_schemas.enums import IssuePriority


class IdentifiedIssue(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    issue: str
    why_it_matters: str
    supporting_fact_descriptions: list[str] = Field(default_factory=list)
    missing_fact_descriptions: list[str] = Field(default_factory=list)
    priority: IssuePriority = IssuePriority.MEDIUM


class IssueIdentificationResult(BaseModel):
    issues: list[IdentifiedIssue] = Field(default_factory=list)
