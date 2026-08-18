"""Legal analysis service — Stage 4."""

from uuid import UUID

from app.llm.base import LLMProvider
from app.services.legal_analyzer_models import LegalAnalysisResult
from app.services.legal_retriever import RetrievalResult
from nyayalens_schemas.enums import ConfidenceLevel, StatementType
from nyayalens_schemas.models import Citation, Fact, Issue, LegalAnalysis, LegalProvision, LegalSource

LEGAL_ANALYSIS_SYSTEM_PROMPT = """You are a legal analysis assistant for Indian law.
Analyze how retrieved legal provisions MAY apply to the case facts.

CRITICAL DISTINCTIONS — label your reasoning:
- FACT: directly from user input
- INFERENCE: logical deduction
- LEGAL SOURCE: from retrieved provision only
- Never invent legal sections not provided in RETRIEVED SOURCES.

RULES:
- Use hedged language: "may", "potentially", "depends on..."
- Note uncertainty and counterarguments for each provision.
- If a provision may not apply, say so.
- Do not declare anyone legally guilty or certainly liable.
"""


class LegalAnalyzerService:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def analyze(
        self,
        description: str,
        issues: list[Issue],
        facts: list[Fact],
        retrieved: list[RetrievalResult],
    ) -> list[LegalAnalysis]:
        if not issues:
            return []

        sources_text = "\n\n".join(
            f"[ID: {r.source.id}] {r.source.title} — {r.source.section or 'N/A'}\n{r.source.text}"
            for r in retrieved
        ) or "No sources retrieved."

        issues_text = "\n".join(f"[ID: {i.id}] {i.issue}" for i in issues)
        facts_text = "\n".join(f"- {f.description}" for f in facts)

        prompt = f"""CASE:
{description}

FACTS:
{facts_text}

ISSUES:
{issues_text}

RETRIEVED SOURCES (use ONLY these — do not cite others):
{sources_text}

For each issue, explain which retrieved provisions may apply and why."""

        result = await self.llm.generate_structured(
            prompt=prompt,
            response_model=LegalAnalysisResult,
            system_prompt=LEGAL_ANALYSIS_SYSTEM_PROMPT,
        )

        source_map: dict[UUID, LegalSource] = {r.source.id: r.source for r in retrieved}
        analyses: list[LegalAnalysis] = []

        for item in result.analyses:
            provisions: list[LegalProvision] = []
            for prov in item.provisions:
                source = source_map.get(prov.legal_source_id)
                if not source:
                    continue
                provisions.append(
                    LegalProvision(
                        legal_source=source,
                        explanation=prov.explanation,
                        applicability=prov.applicability,
                        uncertainty=prov.uncertainty,
                        counterarguments=prov.counterarguments,
                        confidence=prov.confidence,
                        citations=[
                            Citation(
                                legal_source_id=source.id,
                                claim=prov.claim,
                                quoted_text=source.text[:300],
                                is_verified=True,
                                verification_note="Source exists in knowledge base.",
                                statement_type=StatementType.LEGAL_SOURCE,
                            )
                        ],
                    )
                )

            analyses.append(
                LegalAnalysis(
                    issue_id=item.issue_id,
                    provisions=provisions,
                    summary=item.summary,
                    overall_confidence=item.overall_confidence,
                )
            )

        return analyses
