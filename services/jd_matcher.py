"""Deterministic job-description vs resume matcher.

Reuses the existing skill normalisation in recommendation_service.
No metrics are invented: only keywords that appear in the JD are checked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from models.analysis import ResumeAnalysis


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]+", " ", value.casefold()).strip()


def _tokenize(text: str) -> set[str]:
    """Split text into normalized word-tokens of length ≥ 2."""
    raw = re.findall(r"[a-z0-9][a-z0-9+#./]*", text.casefold())
    return {t for t in raw if len(t) >= 2}


def _extract_jd_keywords(jd_text: str) -> list[str]:
    """Return a deduped list of apparent skill/keyword phrases from the JD.

    Strategy: grab words/phrases that look like technology or skills by
    looking for CamelCase tokens, known patterns, and all-cap acronyms,
    plus any 1–3-word sequences preceded by require/must/preferred/need.
    """
    tokens: dict[str, str] = {}  # normalized -> original

    # Single words: CamelCase, all-caps acronyms 2-8 chars, or alphanumeric
    for match in re.finditer(r"\b([A-Z]{2,8}|[A-Z][a-z]+(?:[A-Z][a-z]+)+|[a-zA-Z][a-zA-Z0-9+#./]{1,})\b", jd_text):
        word = match.group()
        key = _normalize(word)
        if key and key not in {"the", "and", "for", "with", "that", "this", "are", "you", "have",
                               "will", "our", "team", "role", "your", "from", "they", "able",
                               "work", "knowledge", "skills", "experience", "years", "required",
                               "preferred", "must", "should", "can", "also", "about"}:
            tokens[key] = word

    # Phrases after "experience with / in", "knowledge of", "proficient in", etc.
    phrase_pat = re.compile(
        r"(?:experience (?:with|in)|knowledge of|proficient in|expertise in|familiar with|"
        r"working knowledge of|hands[- ]on (?:experience )?(?:with|in))\s+"
        r"((?:[A-Za-z][A-Za-z0-9+#./]*\s?){1,4})",
        re.IGNORECASE,
    )
    for m in phrase_pat.finditer(jd_text):
        phrase = m.group(1).strip()
        key = _normalize(phrase)
        if key:
            tokens[key] = phrase

    return list(tokens.values())


@dataclass(frozen=True, slots=True)
class RewriteSuggestion:
    original_bullet: str
    improved_bullet: str
    reason: str
    rule: str  # the invariant: no metrics invented


@dataclass(frozen=True, slots=True)
class JDMatchResult:
    score: int                         # 0-100
    matched_keywords: tuple[str, ...]
    missing_keywords: tuple[str, ...]
    all_jd_keywords: tuple[str, ...]
    rewrite_suggestions: tuple[RewriteSuggestion, ...]


# ---------------------------------------------------------------------------
# Before/after rewrite templates – no invented metrics, only structural advice
# ---------------------------------------------------------------------------

_REWRITE_RULES: list[tuple[re.Pattern[str], str, str, str]] = [
    (
        re.compile(r"^(?:worked on|helped with|assisted with|involved in)\b", re.IGNORECASE),
        "Start with a strong action verb (e.g. 'Designed', 'Implemented', 'Led') to show ownership.",
        "Replace weak openers with action verbs",
        "Action verb rule: bullets must open with an active verb showing ownership.",
    ),
    (
        re.compile(r"^(?:responsible for|in charge of)\b", re.IGNORECASE),
        "Describe the action you took, not the responsibility you held.",
        "Replace 'responsible for' with the action taken",
        "Ownership rule: describe what you did, not what you were told to do.",
    ),
    (
        re.compile(r"\b(?:various|several|many|some|multiple)\b", re.IGNORECASE),
        "Replace vague quantifiers ('various', 'several') with concrete scope where truthful.",
        "Remove vague quantifiers",
        "Specificity rule: vague quantifiers weaken impact — be concrete or omit.",
    ),
    (
        re.compile(r"\bteam player\b|\bself[- ]starter\b|\bfast learner\b|\bgo[- ]getter\b", re.IGNORECASE),
        "Show the trait through a concrete example rather than naming it.",
        "Replace filler soft-skill phrases with evidence",
        "Show-don't-tell rule: demonstrate traits with outcomes, not labels.",
    ),
]


def _suggest_rewrites(resume_text: str, max_suggestions: int = 3) -> list[RewriteSuggestion]:
    """Return up to max_suggestions before/after pairs from actual resume bullets."""
    suggestions: list[RewriteSuggestion] = []
    bullets = [
        line.strip()
        for line in resume_text.splitlines()
        if re.match(r"^\s*[-•*]\s+\S", line) and len(line.strip()) > 20
    ]
    for bullet in bullets:
        clean = re.sub(r"^[-•*]\s+", "", bullet.strip())
        for pattern, advice, label, rule in _REWRITE_RULES:
            if pattern.search(clean):
                improved = pattern.sub("", clean).strip()
                improved = improved[:1].upper() + improved[1:] if improved else clean
                suggestions.append(
                    RewriteSuggestion(
                        original_bullet=clean,
                        improved_bullet=f"[{label}] {improved}",
                        reason=advice,
                        rule=rule,
                    )
                )
                break  # one suggestion per bullet
        if len(suggestions) >= max_suggestions:
            break
    return suggestions


def match_jd(
    resume_text: str,
    analysis: ResumeAnalysis,
    jd_text: str,
) -> JDMatchResult:
    """Score the resume against the JD using keyword intersection."""
    jd_keywords = _extract_jd_keywords(jd_text)
    if not jd_keywords:
        return JDMatchResult(0, (), (), (), ())

    resume_tokens = _tokenize(resume_text)
    # also add skill names from the AI analysis for better coverage
    for skill in analysis.skills:
        resume_tokens.update(_tokenize(skill.name))

    matched: list[str] = []
    missing: list[str] = []
    for kw in jd_keywords:
        kw_tokens = _tokenize(kw)
        if not kw_tokens:
            continue
        # keyword matches if any of its tokens appear in the resume tokens
        if kw_tokens & resume_tokens:
            matched.append(kw)
        else:
            missing.append(kw)

    score = round(len(matched) / len(jd_keywords) * 100) if jd_keywords else 0
    rewrites = _suggest_rewrites(resume_text)
    return JDMatchResult(
        score=score,
        matched_keywords=tuple(matched),
        missing_keywords=tuple(missing),
        all_jd_keywords=tuple(jd_keywords),
        rewrite_suggestions=tuple(rewrites),
    )
