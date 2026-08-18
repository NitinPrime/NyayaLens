"""Grounded mock should use the user's facts, not loan-template text."""

from uuid import uuid4

from app.llm.grounded_mock import build_structured, extract, generate_text
from app.services.argument_analyzer_models import ArgumentAnalysisResult
from app.services.case_parser_models import CaseParseResult
from app.services.classification import ClassificationResult
from app.services.issue_identifier_models import IssueIdentificationResult
from app.services.legal_analyzer_models import LegalAnalysisResult

FRIDGE = """
CASE DESCRIPTION:
I bought a Samsung refrigerator from an Amazon seller, HomeCool Appliances, on 12 March 2026 for ₹48,500.
It was delivered to my flat in Pune on 15 March 2026. Within 11 days the cooling failed and water started leaking.
Samsung’s service centre recorded a manufacturing defect in the compressor. The seller refused a refund, saying
the 7-day return window had expired.

Parties involved: Priya Sharma (buyer), HomeCool Appliances (seller), Amazon (marketplace)
Amount involved: ₹48,500
Evidence available: Invoice, credit-card statement, Samsung service report
Additional context: Used only at home, not for business.
"""


def test_extracts_named_parties_and_amount():
    ex = extract(FRIDGE)
    names = {p[0].lower() for p in ex.parties}
    assert "priya sharma" in names
    assert "homecool appliances" in names
    assert any("48,500" in a or "48500" in a.replace(",", "") for a in ex.amounts)
    assert ex.category == "consumer"


def test_parse_uses_real_names_not_buyer_seller_only():
    parsed = build_structured(CaseParseResult, FRIDGE)
    names = {p.name.lower() for p in parsed.parties}
    assert "priya sharma" in names
    assert any("refrigerator" in f.description.lower() or "compressor" in f.description.lower() for f in parsed.facts)


def test_consumer_arguments_are_not_loan_templates():
    args = build_structured(ArgumentAnalysisResult, FRIDGE)
    blob = " ".join(args.respondent.possible_defenses + args.respondent.strongest_arguments).lower()
    assert "gift" not in blob
    assert "settled account" not in blob
    assert "warranty" in blob or "return window" in blob or "7-day" in blob
    claim = " ".join(args.claimant.strongest_arguments).lower()
    assert "48,500" in claim or "compressor" in claim or "defect" in claim


def test_issues_mention_this_sale():
    issues = build_structured(IssueIdentificationResult, FRIDGE)
    text = " ".join(i.issue for i in issues.issues).lower()
    assert "homecool" in text or "48,500" in text or "refrigerator" in text


def test_classification_summary_is_specific():
    result = build_structured(ClassificationResult, FRIDGE)
    assert "refrigerator" in result.summary.lower() or "48,500" in result.summary
    assert "consumer" in " ".join(d.value for d in result.domains)


def test_legal_analysis_ties_section_38_to_refund():
    source_id = uuid4()
    issue_id = uuid4()
    prompt = f"""CASE DESCRIPTION:
{FRIDGE}

ISSUES:
[ID: {issue_id}] Whether the seller is liable for a defective refrigerator

RETRIEVED SOURCES:
[ID: {source_id}] Consumer Protection Act, 2019 — Section 38
The District Commission may direct the opposite party to remove the defect, replace the goods, return the price paid, or pay compensation.
"""
    result = build_structured(LegalAnalysisResult, prompt)
    explanation = result.analyses[0].provisions[0].explanation.lower()
    assert "48,500" in explanation or "defect" in explanation
    assert "this provision may be relevant depending on whether the factual elements are proved" not in explanation


def test_chat_mentions_return_window_when_asked():
    text = generate_text(
        f"{FRIDGE}\nUSER QUESTION:\nDoes the 7-day return window kill my consumer case?"
    )
    assert "return window" in text.lower() or "statutory" in text.lower()
    assert "gift" not in text.lower()
