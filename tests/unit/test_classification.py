"""Classification keyword tests."""

from app.services.classification import ClassificationService
from nyayalens_schemas.enums import LegalDomain


def test_tenancy_keywords():
    svc = ClassificationService(llm=None)  # type: ignore[arg-type]
    domains = svc.classify_keywords(
        "My landlord refuses to return my security deposit after I moved out."
    )
    assert LegalDomain.TENANCY in domains


def test_consumer_keywords():
    svc = ClassificationService(llm=None)  # type: ignore[arg-type]
    domains = svc.classify_keywords("The seller refused a refund for a defective laptop.")
    assert LegalDomain.CONSUMER in domains


def test_unknown_defaults_to_other():
    svc = ClassificationService(llm=None)  # type: ignore[arg-type]
    domains = svc.classify_keywords("Something happened yesterday.")
    assert domains == [LegalDomain.OTHER]
