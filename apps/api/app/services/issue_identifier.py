"""Issue identification service — Stage 2."""

from uuid import UUID

from app.llm.base import LLMProvider
from app.services.issue_identifier_models import IdentifiedIssue, IssueIdentificationResult
from nyayalens_schemas.enums import IssuePriority
from nyayalens_schemas.models import Fact, Issue

ISSUE_SYSTEM_PROMPT = """You are a legal issue identification assistant for Indian law.
Given structured case facts, identify possible legal issues — not conclusions.

RULES:
- Each issue must be a question or legal problem, not a verdict.
- Tie issues to stated facts; do not invent facts.
- Explain why each issue matters.
- List missing facts that could change the analysis.
- Use neutral language: "whether...", "potential...", "may..."
- Never declare guilt, liability, or certain victory.
"""


class IssueIdentifierService:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def identify(
        self,
        description: str,
        case_type: str | None,
        facts: list[Fact],
        unknown_facts: list[str],
    ) -> list[Issue]:
        facts_text = "\n".join(f"- [{f.fact_type.value}] {f.description}" for f in facts)
        unknown_text = "\n".join(f"- {u}" for u in unknown_facts) if unknown_facts else "None listed"

        prompt = f"""CASE TYPE: {case_type or 'Unknown'}

CASE DESCRIPTION:
{description}

EXTRACTED FACTS:
{facts_text}

KNOWN MISSING FACTS:
{unknown_text}

Identify the key legal issues for this case under Indian law."""

        result = await self.llm.generate_structured(
            prompt=prompt,
            response_model=IssueIdentificationResult,
            system_prompt=ISSUE_SYSTEM_PROMPT,
        )

        fact_map = {f.description.lower(): f.id for f in facts}
        issues: list[Issue] = []
        for item in result.issues:
            supporting_ids: list[UUID] = []
            for desc in item.supporting_fact_descriptions:
                fid = fact_map.get(desc.lower())
                if fid:
                    supporting_ids.append(fid)
                else:
                    for fact in facts:
                        if desc.lower() in fact.description.lower() or fact.description.lower() in desc.lower():
                            supporting_ids.append(fact.id)
                            break

            issues.append(
                Issue(
                    id=item.id,
                    issue=item.issue,
                    why_it_matters=item.why_it_matters,
                    supporting_fact_ids=list(dict.fromkeys(supporting_ids)),
                    missing_fact_descriptions=item.missing_fact_descriptions,
                    priority=item.priority,
                )
            )
        return issues
