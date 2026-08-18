"""Schema validation tests."""

import pytest
from uuid import uuid4

from nyayalens_schemas.enums import FactType, PartyRole, ConfidenceLevel
from nyayalens_schemas.models import Case, CaseCreate, Fact, Party, Analysis


def test_case_create_validation():
    case = CaseCreate(description="This is a valid case description with enough text.")
    assert case.description.startswith("This is")

    with pytest.raises(Exception):
        CaseCreate(description="short")


def test_case_domain_model():
    case = Case(
        description="Test case description for unit testing purposes.",
        parties=[
            Party(name="Person A", role=PartyRole.CLAIMANT),
            Party(name="Person B", role=PartyRole.RESPONDENT),
        ],
        facts=[
            Fact(description="Money was allegedly transferred", fact_type=FactType.ALLEGED),
        ],
    )
    assert len(case.parties) == 2
    assert len(case.facts) == 1
    assert case.parties[0].role == PartyRole.CLAIMANT


def test_analysis_has_disclaimer():
    analysis = Analysis(case_id=uuid4())
    assert "not a substitute" in analysis.disclaimer.lower()
    assert "qualified advocate" in analysis.disclaimer.lower()


def test_confidence_level_enum():
    assert ConfidenceLevel.HIGH.value == "high"
    assert ConfidenceLevel.INSUFFICIENT_EVIDENCE.value == "insufficient_evidence"
