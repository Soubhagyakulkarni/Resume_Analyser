"""Unit tests for the hybrid JD matcher (keyword + dense semantic embedding)."""

from models.analysis import ResumeAnalysis, Skill
from services.jd_matcher import JDMatchResult, _cosine_similarity, match_jd


def _dummy_analysis() -> ResumeAnalysis:
    return ResumeAnalysis(
        summary="Experienced backend engineer building scalable microservices and APIs.",
        technical_skills=(
            Skill("Python", "evidenced", "Built Python microservices"),
            Skill("Docker", "evidenced", "Containerized applications"),
            Skill("FastAPI", "evidenced", "REST APIs with FastAPI"),
        ),
        soft_skills=(),
        experience_assessment="Solid backend project experience.",
        experience_highlights=(
            "Built distributed microservices architecture",
            "Deployed services using Docker and Kubernetes",
        ),
        learning_suggestions=(),
        resume_improvements=(),
        caveats=(),
    )


def test_cosine_similarity_edge_cases():
    # Identical vectors
    assert abs(_cosine_similarity([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-6
    # Orthogonal vectors
    assert abs(_cosine_similarity([1.0, 0.0], [0.0, 1.0]) - 0.0) < 1e-6
    # Empty or mismatched vectors
    assert _cosine_similarity([], []) == 0.0
    assert _cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert _cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_match_jd_pure_keyword_when_no_embedder():
    resume_text = "Proficient in Python, Docker, and FastAPI."
    analysis = _dummy_analysis()
    jd_text = "We are seeking a Python and Docker specialist with experience in Kubernetes."

    result: JDMatchResult = match_jd(resume_text, analysis, jd_text, embedder=None)

    assert result.score > 0
    assert "Python" in result.matched_keywords
    assert "Docker" in result.matched_keywords
    assert "Kubernetes" in result.missing_keywords
    assert result.keyword_score == result.score
    assert result.semantic_score == result.keyword_score


def test_match_jd_hybrid_scoring_boosts_conceptually_similar_resume():
    resume_text = "Built scalable microservices, container orchestration, and cloud backends."
    analysis = _dummy_analysis()
    # JD uses slightly different wording:
    jd_text = "Looking for a Distributed Systems architect with Cloud Infrastructure expertise."

    # Embedder returns high similarity vectors (cosine sim ~0.85)
    def mock_embedder(text: str) -> list[float]:
        if "Summary" in text or "microservices" in text:
            return [0.8, 0.6, 0.0]
        return [0.75, 0.65, 0.0]

    result: JDMatchResult = match_jd(resume_text, analysis, jd_text, embedder=mock_embedder)

    # Keyword match might be low because words are different, but semantic score is high
    assert result.semantic_score > 0
    assert result.score >= result.keyword_score


def test_match_jd_handles_empty_jd():
    analysis = _dummy_analysis()
    result = match_jd("Some resume", analysis, "")
    assert result.score == 0
    assert result.matched_keywords == ()
    assert result.missing_keywords == ()


def test_match_jd_falls_back_gracefully_on_embedder_failure():
    resume_text = "Python engineer"
    analysis = _dummy_analysis()
    jd_text = "Looking for a Python developer"

    def broken_embedder(_text: str) -> list[float]:
        raise RuntimeError("Quota exceeded or network error")

    result = match_jd(resume_text, analysis, jd_text, embedder=broken_embedder)
    # Should not crash; falls back to pure keyword score
    assert result.score == result.keyword_score
