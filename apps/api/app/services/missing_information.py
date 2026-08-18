"""Missing-information detector — pipeline stage."""

from app.llm.base import LLMProvider
from nyayalens_schemas.enums import IssuePriority
from nyayalens_schemas.models import Issue, MissingInformation

MISSING_SYSTEM_PROMPT = """Identify missing facts that could materially change an Indian legal analysis.
Prioritize HIGH / MEDIUM / LOW.
Do not invent answers to the missing facts.
Do not ask for unnecessary personal identifiers.
"""


class MissingFactDetector:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def from_unknown_and_issues(
        self,
        unknown_facts: list[str],
        issues: list[Issue],
    ) -> list[MissingInformation]:
        items: list[MissingInformation] = []
        for fact in unknown_facts:
            items.append(
                MissingInformation(
                    question=fact,
                    why_it_matters="This information could materially affect the legal analysis.",
                    priority=IssuePriority.HIGH,
                    related_issue_ids=[i.id for i in issues[:2]],
                )
            )
        for issue in issues:
            for missing in issue.missing_fact_descriptions:
                if any(missing.lower() == existing.question.lower() for existing in items):
                    continue
                items.append(
                    MissingInformation(
                        question=missing,
                        why_it_matters=f"Could change the analysis of: {issue.issue}",
                        priority=issue.priority,
                        related_issue_ids=[issue.id],
                    )
                )
        return items
