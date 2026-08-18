"""Case parsing service — Stage 1 of analysis pipeline."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CaseRecord, FactRecord, PartyRecord
from app.llm.base import LLMProvider
from app.services.case_parser_models import CaseParseResult
from nyayalens_schemas.enums import FactType, PartyRole

CASE_PARSER_SYSTEM_PROMPT = """You are a legal case structuring assistant for Indian law.
Your task is to extract structured information from a natural language case description.

CRITICAL RULES:
- Do NOT invent facts that are not stated or reasonably implied.
- Mark facts as "alleged" unless clearly undisputed.
- Identify disputed and unknown facts explicitly.
- Use neutral language; never declare guilt or certainty of outcome.
- Extract parties, dates, amounts, locations when mentioned.
- If information is missing, list it in unknown_facts — do not guess.
"""


class CaseParserService:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def parse(self, description: str) -> CaseParseResult:
        prompt = f"""Analyze the following case description and extract structured information.

CASE DESCRIPTION:
{description}

Extract parties, facts, evidence mentioned, disputed facts, and unknown/missing facts.
Do not infer unsupported facts."""

        return await self.llm.generate_structured(
            prompt=prompt,
            response_model=CaseParseResult,
            system_prompt=CASE_PARSER_SYSTEM_PROMPT,
        )

    async def parse_and_persist(self, case: CaseRecord, db: AsyncSession) -> CaseParseResult:
        result = await self.parse(case.description)

        case.case_type = result.case_type
        case.structured_data = result.model_dump(mode="json")

        for party in result.parties:
            db.add(
                PartyRecord(
                    id=party.id,
                    case_id=case.id,
                    name=party.name,
                    role=PartyRole(party.role),
                    description=party.description,
                )
            )

        for fact in result.facts:
            fact_date = None
            if fact.date:
                try:
                    from datetime import date

                    fact_date = date.fromisoformat(fact.date)
                except ValueError:
                    pass

            db.add(
                FactRecord(
                    id=fact.id,
                    case_id=case.id,
                    description=fact.description,
                    fact_type=FactType(fact.fact_type),
                    fact_date=fact_date,
                    location=fact.location,
                    amount=fact.amount,
                )
            )

        await db.flush()
        return result
