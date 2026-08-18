"""Legal domain classification — pipeline stage."""

from pydantic import BaseModel, Field

from app.llm.base import LLMProvider
from nyayalens_schemas.enums import LegalDomain

CLASSIFY_SYSTEM_PROMPT = """You classify Indian legal situations into domains.
Return only domains that are reasonably indicated by the facts.
Do not invent facts. Use cautious language in the rationale and summary.
Never declare guilt or certain legal outcomes.
"""


class ClassificationResult(BaseModel):
    domains: list[LegalDomain] = Field(default_factory=list)
    rationale: str = ""
    summary: str = ""
    inferred_facts: list[str] = Field(default_factory=list)


KEYWORD_DOMAINS: list[tuple[tuple[str, ...], LegalDomain]] = [
    (("landlord", "tenant", "deposit", "rent", "lease"), LegalDomain.TENANCY),
    (("property", "possession", "immovable"), LegalDomain.PROPERTY),
    (("consumer", "defective", "refund", "warranty", "seller"), LegalDomain.CONSUMER),
    (("salary", "wages", "terminated", "employment", "employer"), LegalDomain.EMPLOYMENT),
    (("upi", "otp", "cyber", "phishing", "personation", "harassment"), LegalDomain.CYBER),
    (("loan", "lent", "borrow", "repay", "contract", "agreement"), LegalDomain.CONTRACT),
    (("limitation", "forum", "procedure"), LegalDomain.CIVIL_PROCEDURE),
]


class ClassificationService:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def classify_keywords(self, text: str) -> list[LegalDomain]:
        lower = text.lower()
        found: list[LegalDomain] = []
        for keywords, domain in KEYWORD_DOMAINS:
            if any(k in lower for k in keywords) and domain not in found:
                found.append(domain)
        return found or [LegalDomain.OTHER]

    async def classify(self, description: str, case_type: str | None = None) -> ClassificationResult:
        prompt = f"""CASE TYPE HINT: {case_type or "unknown"}

CASE DESCRIPTION:
{description}

Classify legal domains, write a short cautious summary, and list only inferences that are clearly labeled as inferences (not stated facts)."""
        result = await self.llm.generate_structured(
            prompt=prompt,
            response_model=ClassificationResult,
            system_prompt=CLASSIFY_SYSTEM_PROMPT,
        )
        if not result.domains:
            result.domains = self.classify_keywords(description)
        if not result.summary:
            result.summary = (
                "Based on the information provided, this appears to be a potential legal dispute. "
                "Further facts are required before any reliable conclusion can be drawn."
            )
        return result
