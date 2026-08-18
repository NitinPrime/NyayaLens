"""Citation validator tests."""

from uuid import uuid4

from app.services.citation_validator import CitationValidator
from nyayalens_schemas.enums import LegalSourceType
from nyayalens_schemas.models import Citation, LegalAnalysis, LegalProvision, LegalSource


def _source(text: str = "All agreements are contracts if they are made by free consent.") -> LegalSource:
    return LegalSource(
        title="Indian Contract Act, 1872",
        source_type=LegalSourceType.ACT,
        section="Section 10",
        text=text,
    )


def test_drops_provisions_not_in_retrieved_set():
    real = _source()
    fake = _source()
    analysis = LegalAnalysis(
        issue_id=uuid4(),
        summary="test",
        provisions=[
            LegalProvision(
                legal_source=fake,
                explanation="Invented section 999 applies.",
                applicability="should be dropped",
                uncertainty="high",
                citations=[Citation(legal_source_id=fake.id, claim="Section 999")],
            )
        ],
    )
    cleaned, unsupported = CitationValidator().validate([analysis], [real])
    assert cleaned[0].provisions == []
    assert unsupported


def test_keeps_retrieved_source():
    source = _source()
    analysis = LegalAnalysis(
        issue_id=uuid4(),
        summary="test",
        provisions=[
            LegalProvision(
                legal_source=source,
                explanation="This provision may apply.",
                applicability="potentially",
                uncertainty="depends on facts",
                citations=[
                    Citation(
                        legal_source_id=source.id,
                        claim="Section 10 may be relevant",
                        quoted_text=source.text[:80],
                    )
                ],
            )
        ],
    )
    cleaned, unsupported = CitationValidator().validate([analysis], [source])
    assert len(cleaned[0].provisions) == 1
    assert cleaned[0].provisions[0].citations[0].is_verified is True
    assert unsupported == []
