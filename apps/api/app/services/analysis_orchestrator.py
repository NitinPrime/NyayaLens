"""Analysis orchestration — explicit pipeline stages."""

from datetime import datetime, timezone
from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import AnalysisRecord, AnalysisRun, CaseRecord
from app.llm.base import get_llm_provider
from app.services.argument_analyzer import ArgumentAnalyzerService
from app.services.case_parser import CaseParserService
from app.services.citation_validator import CitationValidator
from app.services.classification import ClassificationService
from app.services.issue_identifier import IssueIdentifierService
from app.services.legal_analyzer import LegalAnalyzerService
from app.services.legal_retriever import LegalRetriever
from app.services.missing_information import MissingFactDetector
from app.services.recommendation_engine import RecommendationEngine
from nyayalens_schemas.enums import AnalysisStatus, ConfidenceLevel, FactType
from nyayalens_schemas.models import Analysis, Fact

DISCLAIMER = (
    "NyayaLens provides general legal information and AI-assisted case analysis. "
    "It is not a substitute for advice from a qualified advocate. "
    "Legal outcomes depend on facts, evidence, jurisdiction, procedure, and applicable law."
)


class AnalysisOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        settings = get_settings()
        self.model_name = settings.llm_model
        self.llm = get_llm_provider(
            settings.llm_provider,
            api_key=settings.openai_api_key or settings.anthropic_api_key,
            model=settings.llm_model,
        )
        self.case_parser = CaseParserService(self.llm)
        self.classifier = ClassificationService(self.llm)
        self.issue_identifier = IssueIdentifierService(self.llm)
        self.legal_retriever = LegalRetriever(db, self.llm)
        self.legal_analyzer = LegalAnalyzerService(self.llm)
        self.argument_analyzer = ArgumentAnalyzerService(self.llm)
        self.missing_detector = MissingFactDetector(self.llm)
        self.recommendation_engine = RecommendationEngine(self.llm)
        self.citation_validator = CitationValidator()

    async def _log_stage(
        self,
        analysis_id,
        stage: str,
        started: float,
        retrieval_count: int = 0,
        error: str | None = None,
    ) -> None:
        self.db.add(
            AnalysisRun(
                analysis_id=analysis_id,
                stage=stage,
                status="failed" if error else "completed",
                latency_ms=int((perf_counter() - started) * 1000),
                retrieval_count=retrieval_count,
                model_used=self.model_name,
                error=error,
            )
        )

    async def run_analysis(self, case: CaseRecord) -> AnalysisRecord:
        analysis = AnalysisRecord(case_id=case.id, status=AnalysisStatus.IN_PROGRESS)
        self.db.add(analysis)
        await self.db.flush()

        try:
            t = perf_counter()
            parse_result = await self.case_parser.parse_and_persist(case, self.db)
            await self.db.refresh(case, ["parties", "facts"])
            await self._log_stage(analysis.id, "case_structuring", t)

            facts = [
                Fact(id=f.id, description=f.description, fact_type=FactType(f.fact_type))
                for f in case.facts
            ]

            t = perf_counter()
            classification = await self.classifier.classify(case.description, case.case_type)
            if not case.case_type and classification.domains:
                case.case_type = classification.domains[0].value.replace("_", " ")
            await self._log_stage(analysis.id, "classification", t)

            t = perf_counter()
            issues = await self.issue_identifier.identify(
                description=case.description,
                case_type=case.case_type,
                facts=facts,
                unknown_facts=parse_result.unknown_facts,
            )
            await self._log_stage(analysis.id, "issue_extraction", t)

            t = perf_counter()
            retrieved = await self.legal_retriever.search(
                query=case.description,
                issues=[i.issue for i in issues] + [d.value for d in classification.domains],
                limit=6,
            )
            sources = [r.source for r in retrieved]
            await self._log_stage(analysis.id, "legal_retrieval", t, retrieval_count=len(sources))

            t = perf_counter()
            legal_analyses = await self.legal_analyzer.analyze(
                description=case.description,
                issues=issues,
                facts=facts,
                retrieved=retrieved,
            )
            await self._log_stage(analysis.id, "legal_analysis", t)

            t = perf_counter()
            legal_analyses, unsupported = self.citation_validator.validate(legal_analyses, sources)
            await self._log_stage(analysis.id, "citation_validation", t)

            t = perf_counter()
            claimant_arg, respondent_arg = await self.argument_analyzer.analyze(
                description=case.description,
                facts=facts,
                issues=issues,
                legal_analyses=legal_analyses,
                retrieved=retrieved,
            )
            await self._log_stage(analysis.id, "counterarguments", t)

            missing_info = self.missing_detector.from_unknown_and_issues(
                parse_result.unknown_facts, issues
            )

            t = perf_counter()
            recommendations = await self.recommendation_engine.generate(
                case_type=case.case_type,
                issues=issues,
                missing_info=missing_info,
            )
            await self._log_stage(analysis.id, "recommendations", t)

            overall = ConfidenceLevel.MEDIUM
            if not sources:
                overall = ConfidenceLevel.INSUFFICIENT_EVIDENCE
            elif len(missing_info) >= 3:
                overall = ConfidenceLevel.LOW

            uncertainty = (
                "Confidence is limited because key facts are missing, "
                "the knowledge base is a curated demo corpus (not all Indian law), "
                "and outcomes depend on evidence, procedure, and applicable versions of law."
            )
            if unsupported:
                uncertainty += " Some unsupported legal claims were removed or flagged."

            result = Analysis(
                id=analysis.id,
                case_id=case.id,
                status=AnalysisStatus.COMPLETED,
                summary=classification.summary,
                legal_domains=classification.domains,
                inferred_facts=classification.inferred_facts,
                issues=issues,
                legal_analyses=legal_analyses,
                claimant_argument=claimant_arg,
                respondent_argument=respondent_arg,
                missing_information=missing_info,
                recommendations=recommendations,
                retrieved_sources=sources,
                overall_confidence=overall,
                uncertainty_explanation=uncertainty,
                unsupported_claims=unsupported,
                disclaimer=DISCLAIMER,
                completed_at=datetime.now(timezone.utc),
            )

            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.result = result.model_dump(mode="json")
            await self.db.flush()
            return analysis

        except Exception as e:
            analysis.status = AnalysisStatus.FAILED
            analysis.result = {"error": "Analysis failed. Please try again."}
            await self._log_stage(analysis.id, "pipeline", perf_counter(), error=str(e)[:500])
            await self.db.flush()
            raise
