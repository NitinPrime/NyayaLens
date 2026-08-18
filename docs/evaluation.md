# Evaluation Methodology

## Purpose

Measure NyayaLens quality across fact extraction, issue identification, retrieval, citations, and uncertainty handling.

## Evaluation Dataset

Synthetic legal scenarios in `/data/sample_cases/` with:

- Known facts
- Expected legal issues
- Relevant source references
- Expected missing information
- Expected arguments for both sides

## Metrics

| Metric | Description |
|--------|-------------|
| Fact extraction accuracy | % of expected facts correctly extracted |
| Issue identification accuracy | % of expected issues identified |
| Retrieval precision | % of retrieved sources that are relevant |
| Citation support rate | % of legal claims with verified sources |
| Unsupported claim rate | % of claims without source backing |
| Evidence mapping accuracy | % of evidence correctly mapped to facts |
| Argument coverage | % of expected arguments generated |
| Uncertainty correctness | Appropriate hedging in ambiguous cases |

## Evaluation Dashboard

Metrics displayed only from actual evaluation runs — never fabricated.

## Test Scenarios

- Hallucinated citation detection
- Nonexistent section reference
- Irrelevant source retrieval
- Contradictory evidence
- Missing facts handling
- Ambiguous case description
- Insufficient evidence case
- Malicious prompt injection in uploaded documents

## Implementation Status

**Planned:** Evaluation service in `/services/evaluation`
**Current:** Test structure in `/tests/evaluation/` (not yet populated)
