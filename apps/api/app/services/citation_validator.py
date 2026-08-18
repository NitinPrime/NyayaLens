"""Citation validation — drop or flag claims not backed by retrieved sources."""

from nyayalens_schemas.models import LegalAnalysis, LegalSource


class CitationValidator:
    """Ensure legal claims point at sources that were actually retrieved."""

    def validate(
        self,
        legal_analyses: list[LegalAnalysis],
        retrieved_sources: list[LegalSource],
    ) -> tuple[list[LegalAnalysis], list[str]]:
        source_ids = {s.id for s in retrieved_sources}
        source_text = {s.id: s.text.lower() for s in retrieved_sources}
        unsupported: list[str] = []
        cleaned: list[LegalAnalysis] = []

        for analysis in legal_analyses:
            valid_provisions = []
            for provision in analysis.provisions:
                source = provision.legal_source
                if source.id not in source_ids:
                    unsupported.append(
                        f"Removed claim not backed by a retrieved source: {provision.explanation[:160]}"
                    )
                    continue

                for citation in provision.citations:
                    citation.is_verified = citation.legal_source_id in source_ids
                    quoted = (citation.quoted_text or "").strip()
                    if quoted and quoted.lower()[:80] not in source_text[source.id]:
                        # Allow truncated quotes of the stored provision text
                        if source.text[:80].lower() not in quoted.lower() and quoted.lower() not in source_text[source.id]:
                            citation.is_verified = False
                            citation.verification_note = (
                                "Quoted text could not be matched to the retrieved provision."
                            )
                            unsupported.append(
                                "A quoted excerpt could not be verified against the retrieved source."
                            )
                        else:
                            citation.verification_note = "Source exists in the knowledge base."
                    else:
                        citation.verification_note = "Source exists in the knowledge base."
                valid_provisions.append(provision)

            analysis.provisions = valid_provisions
            if not valid_provisions:
                analysis.summary = (
                    (analysis.summary or "")
                    + " NyayaLens could not attach a sufficiently reliable retrieved source to this issue."
                )
            cleaned.append(analysis)

        return cleaned, unsupported
