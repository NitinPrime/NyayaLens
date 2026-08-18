"""Hybrid retrieval scoring tests."""

from app.services.legal_retriever import _keyword_score, _tokenize


class FakeRecord:
    title = "Consumer Protection Act, 2019"
    section = "Section 38"
    text = "The District Commission may direct replacement or refund of the price paid."
    amendment_history = ["consumer", "refund", "defective"]


def test_keyword_score_ranks_overlapping_tokens():
    tokens = _tokenize("consumer refund defective laptop")
    score = _keyword_score(tokens, FakeRecord())  # type: ignore[arg-type]
    assert score > 0.4


def test_unrelated_query_scores_low():
    tokens = _tokenize("astronomy satellite orbit")
    score = _keyword_score(tokens, FakeRecord())  # type: ignore[arg-type]
    assert score < 0.2
