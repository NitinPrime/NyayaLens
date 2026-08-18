"""Next steps recommendation engine — Stage 8 (basic)."""

from app.llm.base import LLMProvider
from nyayalens_schemas.enums import RecommendationPriority
from nyayalens_schemas.models import Issue, MissingInformation, Recommendation

RECOMMENDATION_SYSTEM_PROMPT = """You suggest practical, lawful next steps for someone facing a legal situation in India.

RULES:
- Non-deterministic: "consider", "may wish to", "could"
- No dangerous, unlawful, deceptive, or retaliatory advice.
- Prioritize preserving evidence and consulting a qualified advocate.
- Encourage formal channels where appropriate.
"""


class RecommendationEngine:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate(
        self,
        case_type: str | None,
        issues: list[Issue],
        missing_info: list[MissingInformation],
    ) -> list[Recommendation]:
        issues_text = "\n".join(f"- {i.issue}" for i in issues)
        missing_text = "\n".join(f"- {m.question}" for m in missing_info)

        prompt = f"""CASE TYPE: {case_type or 'General dispute'}

ISSUES:
{issues_text or 'None identified'}

MISSING INFORMATION:
{missing_text or 'None identified'}

Suggest 3-5 practical next steps as a JSON array with fields: action, rationale, priority (high/medium/low).
Return ONLY valid JSON array."""

        text = await self.llm.generate(prompt, RECOMMENDATION_SYSTEM_PROMPT)

        recommendations: list[Recommendation] = []
        defaults = [
            Recommendation(
                action="Preserve all relevant evidence (messages, receipts, contracts, transaction records).",
                rationale="Evidence quality may materially affect any future legal process.",
                priority=RecommendationPriority.HIGH,
            ),
            Recommendation(
                action="Create a dated timeline of events while details are fresh.",
                rationale="Chronology helps identify limitation periods and factual gaps.",
                priority=RecommendationPriority.MEDIUM,
            ),
            Recommendation(
                action="Consult a qualified advocate for advice specific to your situation.",
                rationale="NyayaLens provides general information, not professional legal advice.",
                priority=RecommendationPriority.HIGH,
            ),
        ]

        try:
            import json

            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                items = json.loads(text[start:end])
                for item in items[:5]:
                    recommendations.append(
                        Recommendation(
                            action=item["action"],
                            rationale=item["rationale"],
                            priority=RecommendationPriority(item.get("priority", "medium")),
                        )
                    )
        except Exception:
            pass

        return recommendations or defaults
