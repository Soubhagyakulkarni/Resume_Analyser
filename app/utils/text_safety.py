"""Small helpers for untrusted and bounded text."""

import re

_EVIDENCE_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "using",
    "with",
}


def bounded_text(value: str, limit: int) -> str:
    """Trim surrounding whitespace and truncate to a configured bound."""
    return value.strip()[:limit]


def normalize_tokens(value: str) -> tuple[str, ...]:
    """Normalize text to Unicode-aware alphanumeric tokens."""
    return tuple(re.findall(r"[^\W_]+(?:[+#.]?[^\W_]+)*", value.casefold()))


def evidence_is_supported(evidence: str, source_text: str) -> bool:
    """Accept verbatim evidence or sufficiently overlapping text with punctuation drift.

    Threshold is 0.6 (60%) to accommodate:
    - PDF text extraction artefacts (ligatures, hyphenation, line breaks)
    - LLM paraphrasing of exact resume phrases
    - Mixed-case or punctuation differences

    This still blocks fabricated claims where random words share <60% overlap
    with the source resume text.
    """
    evidence_tokens = tuple(
        token for token in normalize_tokens(evidence) if token not in _EVIDENCE_STOP_WORDS
    )
    source_tokens = set(normalize_tokens(source_text))
    if not evidence_tokens:
        return False
    matching_tokens = sum(token in source_tokens for token in evidence_tokens)
    return matching_tokens / len(evidence_tokens) >= 0.6
