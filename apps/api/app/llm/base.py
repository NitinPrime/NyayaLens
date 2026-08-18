"""LLM provider abstraction layer."""

import re
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class MockLLMProvider(LLMProvider):
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        if "USER QUESTION:" in prompt or (system_prompt and "follow-up" in system_prompt.lower()):
            return (
                "FACT: The question is answered only against the case description you provided.\n"
                "LAW: NyayaLens uses retrieved knowledge-base provisions only and does not invent sections.\n"
                "ANALYSIS: Based on the information provided, additional facts may change this view. "
                "The other side may dispute the characterisation of events.\n"
                "RECOMMENDATION: Preserve evidence and consider consulting a qualified advocate. "
                "This is general information, not legal advice."
            )
        return """[
  {"action": "Preserve all messages, receipts, and transaction records.", "rationale": "Evidence may be essential to prove the claim.", "priority": "high"},
  {"action": "Send a formal written reminder before escalating.", "rationale": "A documented demand may support future proceedings.", "priority": "medium"},
  {"action": "Consult a qualified advocate with your evidence.", "rationale": "Professional advice is needed for strategy and limitation concerns.", "priority": "high"}
]"""

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        return _build_mock_response(response_model, prompt)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        dimension = 64
        vectors = []
        for text in texts:
            tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
            vec = [0.0] * dimension
            for i, token in enumerate(sorted(tokens)):
                vec[i % dimension] += hash(token) % 100 / 100.0
            vectors.append(vec)
        return vectors


def _extract_ids(prompt: str) -> list[UUID]:
    ids = []
    for match in re.findall(
        r"\[ID: ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]",
        prompt,
        re.I,
    ):
        try:
            ids.append(UUID(match))
        except ValueError:
            pass
    return ids


def _case_category(prompt: str) -> str:
    lower = prompt.lower()
    if any(w in lower for w in ["landlord", "tenant", "deposit", "rent", "moved out"]):
        return "tenancy"
    if any(w in lower for w in ["otp", "phishing", "upi fraud", "personation", "harassment", "cyber"]):
        return "cyber"
    if any(w in lower for w in ["consumer", "laptop", "defective", "refund", "seller"]):
        return "consumer"
    if any(w in lower for w in ["employment", "salary", "terminated", "worked", "settlement"]):
        return "employment"
    return "loan"


def _build_mock_response(model: Type[T], prompt: str) -> T:
    from nyayalens_schemas.enums import ConfidenceLevel, FactType, IssuePriority, LegalDomain, PartyRole

    from app.services.argument_analyzer_models import ArgumentAnalysisResult, SideAnalysis
    from app.services.case_parser_models import CaseParseResult
    from app.services.classification import ClassificationResult
    from app.services.issue_identifier_models import IdentifiedIssue, IssueIdentificationResult
    from app.services.legal_analyzer_models import AnalyzedProvision, IssueLegalAnalysis, LegalAnalysisResult

    name = model.__name__
    category = _case_category(prompt)

    if name == "ClassificationResult":
        domain_map = {
            "tenancy": [LegalDomain.TENANCY, LegalDomain.PROPERTY, LegalDomain.CONSUMER],
            "cyber": [LegalDomain.CYBER, LegalDomain.CRIMINAL],
            "consumer": [LegalDomain.CONSUMER, LegalDomain.CONTRACT],
            "employment": [LegalDomain.EMPLOYMENT],
            "loan": [LegalDomain.CONTRACT, LegalDomain.CIVIL_PROCEDURE],
        }
        summary_map = {
            "tenancy": "Based on the information provided, this may involve a tenancy or security-deposit dispute.",
            "cyber": "Based on the information provided, this may involve online fraud, identity misuse, or cyber harassment.",
            "consumer": "Based on the information provided, this may involve a consumer goods or services dispute.",
            "employment": "Based on the information provided, this may involve unpaid wages or termination.",
            "loan": "Based on the information provided, this may involve a contractual or money-recovery dispute.",
        }
        return ClassificationResult(
            domains=domain_map.get(category, [LegalDomain.OTHER]),
            rationale="Classification is based on keywords and stated facts only.",
            summary=summary_map.get(category, summary_map["loan"]),
            inferred_facts=["The other party's legal characterisation of the events has not been heard."],
        )

    if name == "CaseParseResult":
        if category == "tenancy":
            return model(
                case_type="Potential tenancy / security deposit dispute",
                parties=[
                    {"name": "Tenant", "role": PartyRole.CLAIMANT.value, "description": "Former occupant seeking deposit return"},
                    {"name": "Landlord", "role": PartyRole.RESPONDENT.value, "description": "Person alleged to be withholding the deposit"},
                ],
                facts=[
                    {"description": "A security deposit was allegedly paid", "fact_type": FactType.ALLEGED.value},
                    {"description": "The occupant allegedly vacated the premises", "fact_type": FactType.ALLEGED.value},
                    {"description": "The deposit is allegedly being withheld", "fact_type": FactType.DISPUTED.value},
                ],
                evidence_mentioned=["possible rental agreement", "payment records"],
                disputed_facts=["Whether damage or unpaid dues justify withholding"],
                unknown_facts=["Whether there was a written rental agreement", "Whether an inspection was performed"],
            )
        if category == "cyber":
            return model(
                case_type="Potential cyber / online fraud dispute",
                parties=[
                    {"name": "Complainant", "role": PartyRole.CLAIMANT.value, "description": "Person alleging online fraud or harassment"},
                    {"name": "Unknown actor", "role": PartyRole.RESPONDENT.value, "description": "Person or account alleged to have caused the harm"},
                ],
                facts=[
                    {"description": "An online communication or payment was allegedly involved", "fact_type": FactType.ALLEGED.value},
                    {"description": "Loss, impersonation, or harassment is alleged", "fact_type": FactType.ALLEGED.value},
                ],
                evidence_mentioned=["screenshots", "transaction records", "messages"],
                disputed_facts=["Identity of the actor", "Whether consent was obtained"],
                unknown_facts=["Exact platform used", "Whether a police/cyber complaint was filed"],
            )
        if category == "consumer":
            return model(
                case_type="Potential consumer dispute",
                parties=[
                    {"name": "Buyer", "role": PartyRole.CLAIMANT.value, "description": "Purchaser of goods"},
                    {"name": "Seller", "role": PartyRole.RESPONDENT.value, "description": "Online seller"},
                ],
                facts=[
                    {"description": "Goods were purchased for consideration", "fact_type": FactType.ALLEGED.value},
                    {"description": "Alleged defect appeared within a short period", "fact_type": FactType.ALLEGED.value},
                    {"description": "Refund was allegedly refused", "fact_type": FactType.DISPUTED.value},
                ],
                evidence_mentioned=["invoice", "payment receipt", "email correspondence"],
                disputed_facts=["Whether defect existed at delivery"],
                unknown_facts=["Exact warranty terms", "Whether repair was attempted"],
            )
        if category == "employment":
            return model(
                case_type="Potential employment / wages dispute",
                parties=[
                    {"name": "Employee", "role": PartyRole.CLAIMANT.value, "description": "Former employee"},
                    {"name": "Employer", "role": PartyRole.RESPONDENT.value, "description": "Company/startup"},
                ],
                facts=[
                    {"description": "Employment allegedly continued for over a year", "fact_type": FactType.ALLEGED.value},
                    {"description": "Termination allegedly occurred without notice", "fact_type": FactType.ALLEGED.value},
                    {"description": "Salary and settlement allegedly remain unpaid", "fact_type": FactType.DISPUTED.value},
                ],
                evidence_mentioned=["salary slips", "email communications"],
                disputed_facts=["Whether employment terms were agreed orally only"],
                unknown_facts=["Written contract existence", "Exact amount owed"],
            )
        return model(
            case_type="Potential contractual / money dispute",
            parties=[
                {"name": "Person A", "role": PartyRole.CLAIMANT.value, "description": "Potential claimant/lender"},
                {"name": "Person B", "role": PartyRole.RESPONDENT.value, "description": "Potential respondent/borrower"},
            ],
            facts=[
                {"description": "Money was allegedly transferred between parties", "fact_type": FactType.ALLEGED.value},
                {"description": "Repayment was allegedly promised", "fact_type": FactType.ALLEGED.value},
                {"description": "Repayment is allegedly being refused", "fact_type": FactType.DISPUTED.value},
            ],
            evidence_mentioned=["UPI transaction", "WhatsApp messages"],
            disputed_facts=["Whether the transfer was a loan or gift"],
            unknown_facts=["Exact repayment deadline", "Whether interest was agreed"],
        )

    if name == "IssueIdentificationResult":
        if category == "tenancy":
            issues = [
                IdentifiedIssue(
                    issue="Whether withholding the security deposit is legally permissible on these facts",
                    why_it_matters="Deposit refund often depends on the agreement, deductions, and condition of the premises.",
                    supporting_fact_descriptions=["A security deposit was allegedly paid", "The deposit is allegedly being withheld"],
                    missing_fact_descriptions=["Whether there was a written rental agreement", "Whether an inspection was performed"],
                    priority=IssuePriority.HIGH,
                ),
                IdentifiedIssue(
                    issue="What forum or process may be appropriate to seek return of the deposit",
                    why_it_matters="Civil, consumer, or tenancy-specific routes may depend on the facts and local law.",
                    priority=IssuePriority.MEDIUM,
                ),
            ]
        elif category == "cyber":
            issues = [
                IdentifiedIssue(
                    issue="Whether the alleged conduct may engage cyber or cheating-related provisions",
                    why_it_matters="Classification affects evidence, complaint routes, and urgency.",
                    missing_fact_descriptions=["Exact platform used", "Whether a police/cyber complaint was filed"],
                    priority=IssuePriority.HIGH,
                ),
                IdentifiedIssue(
                    issue="What evidence should be preserved for any future complaint",
                    why_it_matters="Electronic records often determine whether a claim can be substantiated.",
                    priority=IssuePriority.MEDIUM,
                ),
            ]
        elif category == "consumer":
            issues = [
                IdentifiedIssue(
                    issue="Whether the seller is liable for a defective product",
                    why_it_matters="Consumer remedies depend on defect and deficiency being established.",
                    supporting_fact_descriptions=["Goods were purchased for consideration", "Alleged defect appeared within a short period"],
                    missing_fact_descriptions=["Exact warranty terms"],
                    priority=IssuePriority.HIGH,
                ),
                IdentifiedIssue(
                    issue="What remedies may be available to the consumer",
                    why_it_matters="Relief may include repair, replacement, refund, or compensation depending on facts.",
                    priority=IssuePriority.MEDIUM,
                ),
            ]
        elif category == "employment":
            issues = [
                IdentifiedIssue(
                    issue="Whether unpaid wages or terminal benefits are owed",
                    why_it_matters="Payment obligations depend on employment terms and applicable wage laws.",
                    supporting_fact_descriptions=["Salary and settlement allegedly remain unpaid"],
                    missing_fact_descriptions=["Written contract existence", "Exact amount owed"],
                    priority=IssuePriority.HIGH,
                ),
                IdentifiedIssue(
                    issue="Whether termination complied with applicable requirements",
                    why_it_matters="Notice and payment timelines may affect the employer's liability.",
                    supporting_fact_descriptions=["Termination allegedly occurred without notice"],
                    priority=IssuePriority.MEDIUM,
                ),
            ]
        else:
            issues = [
                IdentifiedIssue(
                    issue="Whether a legally enforceable repayment obligation existed",
                    why_it_matters="Recovery generally requires proving agreement and breach, not merely transfer of money.",
                    supporting_fact_descriptions=["Money was allegedly transferred between parties", "Repayment was allegedly promised"],
                    missing_fact_descriptions=["Exact repayment deadline", "Whether the transfer was a loan or gift"],
                    priority=IssuePriority.HIGH,
                ),
                IdentifiedIssue(
                    issue="Whether limitation or procedural bars may apply",
                    why_it_matters="Delay can affect whether a claim remains actionable.",
                    priority=IssuePriority.MEDIUM,
                ),
            ]
        return model(issues=issues)

    if name == "LegalAnalysisResult":
        issue_block = prompt.split("ISSUES:")[-1].split("RETRIEVED SOURCES")[0] if "ISSUES:" in prompt else prompt
        source_block = prompt.split("RETRIEVED SOURCES")[-1] if "RETRIEVED SOURCES" in prompt else prompt
        issue_ids = _extract_ids(issue_block) or [uuid4()]
        source_ids = _extract_ids(source_block) or [uuid4()]

        analyses = []
        for issue_id in issue_ids[:2]:
            provisions = []
            for sid in source_ids[:2]:
                provisions.append(
                    AnalyzedProvision(
                        legal_source_id=sid,
                        explanation="This provision may be relevant depending on whether the factual elements are proved.",
                        applicability="Potentially applicable if the required facts and legal conditions are established.",
                        uncertainty="Outcome depends on evidence and facts not yet confirmed.",
                        counterarguments=["The other party may argue different facts or a different legal characterization."],
                        confidence=ConfidenceLevel.MEDIUM,
                        claim="Based on the facts provided, this provision may support part of the analysis.",
                    )
                )
            analyses.append(
                IssueLegalAnalysis(
                    issue_id=issue_id,
                    summary="Based on the facts provided, further evidence is needed before a reliable conclusion can be drawn.",
                    provisions=provisions,
                    overall_confidence=ConfidenceLevel.MEDIUM,
                )
            )
        return model(analyses=analyses)

    if name == "ArgumentAnalysisResult":
        return model(
            claimant=SideAnalysis(
                position="Claimant / user position",
                strongest_arguments=[
                    "Based on the facts provided, there may be a recoverable claim if obligation and breach are proved.",
                    "Documentary evidence such as messages or receipts may support the claim.",
                ],
                weaknesses=[
                    "Missing facts could weaken proof of obligation or timing.",
                    "The other side may dispute characterization of the transaction or events.",
                ],
                confidence=ConfidenceLevel.MEDIUM,
            ),
            respondent=SideAnalysis(
                position="Opposing / respondent position",
                strongest_arguments=[
                    "The respondent may argue no enforceable obligation arose on these facts.",
                    "Alternative explanations for payment or conduct may exist.",
                ],
                possible_defenses=[
                    "Denial of promise or agreement.",
                    "Claim that transfer was a gift or settled account.",
                    "Limitation or lack of proof.",
                ],
                weaknesses=[
                    "Documentary evidence may undermine denial if messages or receipts exist.",
                ],
                confidence=ConfidenceLevel.MEDIUM,
            ),
        )

    try:
        return model()
    except Exception:
        fields = {}
        for field_name, field_info in model.model_fields.items():
            if field_info.default is not None:
                fields[field_name] = field_info.default
            elif field_info.default_factory is not None:
                fields[field_name] = field_info.default_factory()
        return model(**fields)


def get_llm_provider(provider_name: str, **kwargs: Any) -> LLMProvider:
    if provider_name == "mock":
        return MockLLMProvider()
    if provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(**kwargs)
    if provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(**kwargs)
    raise ValueError(f"Unknown LLM provider: {provider_name}")
