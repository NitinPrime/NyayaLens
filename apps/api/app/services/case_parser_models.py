"""Structured output models for case parsing pipeline."""

from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from nyayalens_schemas.enums import FactType, PartyRole


class ParsedParty(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    role: PartyRole = PartyRole.UNKNOWN
    description: Optional[str] = None


class ParsedFact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    description: str
    fact_type: FactType = FactType.ALLEGED
    date: Optional[str] = None
    location: Optional[str] = None
    amount: Optional[str] = None


class CaseParseResult(BaseModel):
    case_type: Optional[str] = None
    parties: list[ParsedParty] = Field(default_factory=list)
    facts: list[ParsedFact] = Field(default_factory=list)
    evidence_mentioned: list[str] = Field(default_factory=list)
    disputed_facts: list[str] = Field(default_factory=list)
    unknown_facts: list[str] = Field(default_factory=list)
