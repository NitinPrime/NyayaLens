"""Both-side argument analysis — Stage 5."""

from uuid import UUID

from app.llm.base import LLMProvider
from app.services.argument_analyzer_models import ArgumentAnalysisResult
from app.services.legal_retriever import RetrievalResult
from nyayalens_schemas.models import Argument, Fact, Issue, LegalAnalysis

ARGUMENT_SYSTEM_PROMPT = """You are a legal argument analysis assistant for Indian law.
Analyze the case from BOTH sides fairly.

RULES:
- Do NOT optimize for agreeing with the user/claimant.
- Actively identify weaknesses in the claimant's position.
- Identify possible defenses for the respondent.
- Use hedged language; never declare certain victory or guilt.
- Base arguments on stated facts and retrieved legal sources only.
- Separate facts from assumptions and legal conclusions.
"""


class ArgumentAnalyzerService:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def analyze(
        self,
        description: str,
        facts: list[Fact],
        issues: list[Issue],
        legal_analyses: list[LegalAnalysis],
        retrieved: list[RetrievalResult],
    ) -> tuple[Argument, Argument]:
        facts_text = "\n".join(f"- {f.description}" for f in facts)
        issues_text = "\n".join(f"- {i.issue}" for i in issues)
        law_text = "\n".join(
            f"- {r.source.title} {r.source.section}: {r.source.text[:200]}..."
            for r in retrieved[:5]
        )
        analysis_text = "\n".join(f"- {a.summary}" for a in legal_analyses)

        prompt = f"""CASE:
{description}

FACTS:
{facts_text}

ISSUES:
{issues_text}

LEGAL ANALYSIS SUMMARY:
{analysis_text}

RELEVANT LAW:
{law_text}

Provide strongest arguments for the claimant/user position AND the opposing/respondent position.
Include weaknesses for each side."""

        result = await self.llm.generate_structured(
            prompt=prompt,
            response_model=ArgumentAnalysisResult,
            system_prompt=ARGUMENT_SYSTEM_PROMPT,
        )

        source_ids = [r.source.id for r in retrieved[:5]]
        fact_ids = [f.id for f in facts]

        claimant = Argument(
            position=result.claimant.position,
            strongest_arguments=result.claimant.strongest_arguments,
            supporting_fact_ids=fact_ids,
            supporting_source_ids=source_ids,
            weaknesses=result.claimant.weaknesses,
            confidence=result.claimant.confidence,
        )
        respondent = Argument(
            position=result.respondent.position,
            strongest_arguments=result.respondent.strongest_arguments,
            possible_defenses=result.respondent.possible_defenses,
            supporting_fact_ids=fact_ids,
            supporting_source_ids=source_ids,
            weaknesses=result.respondent.weaknesses,
            confidence=result.respondent.confidence,
        )
        return claimant, respondent
