"""Analysis orchestration and resume-evidence validation."""

import logging

from app.utils.text_safety import evidence_is_supported
from models.analysis import ImprovementSuggestion, ResumeAnalysis, Skill
from services.ports import AnalysisGateway

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, gateway: AnalysisGateway) -> None:
        self._gateway = gateway

    def analyze(self, resume_text: str) -> ResumeAnalysis:
        analysis = self._gateway.analyze(resume_text)

        # For skills the model marked as stated (not inferred): verify the
        # evidence actually appears in the resume text at ≥60% token overlap.
        # If it does not — common with PDF extraction artefacts (ligatures,
        # hyphenation, line breaks) or LLM paraphrasing — downgrade the skill
        # to inferred=True rather than aborting the entire analysis.
        # Per PRD FR-14: inferred skills must be labelled, not silently dropped
        # or treated as a fatal error.
        corrected_technical: list[Skill] = []
        for skill in analysis.technical_skills:
            if not skill.inferred and not evidence_is_supported(skill.evidence, resume_text):
                logger.warning(
                    "Skill evidence has low overlap with source resume; downgrading to inferred"
                )
                corrected_technical.append(
                    Skill(name=skill.name, evidence=skill.evidence, inferred=True)
                )
            else:
                corrected_technical.append(skill)

        corrected_soft: list[Skill] = []
        for skill in analysis.soft_skills:
            if not skill.inferred and not evidence_is_supported(skill.evidence, resume_text):
                logger.warning(
                    "Soft skill evidence has low overlap; downgrading to inferred skill=%r",
                    skill.name,
                )
                corrected_soft.append(
                    Skill(name=skill.name, evidence=skill.evidence, inferred=True)
                )
            else:
                corrected_soft.append(skill)

        # For improvement suggestions: if the evidence phrase has low resume
        # overlap it means the model referenced text that was not clearly
        # present in the extracted resume — often due to PDF extraction
        # artefacts rather than fabrication. Clear the evidence field so the
        # suggestion still appears (with its issue and recommendation intact)
        # but without a potentially misleading evidence reference.
        corrected_suggestions: list[ImprovementSuggestion] = []
        for suggestion in analysis.resume_improvements:
            if suggestion.evidence and not evidence_is_supported(suggestion.evidence, resume_text):
                logger.warning(
                    "Suggestion evidence has low resume overlap; clearing evidence field"
                )
                corrected_suggestions.append(
                    ImprovementSuggestion(
                        priority=suggestion.priority,
                        issue=suggestion.issue,
                        recommendation=suggestion.recommendation,
                        evidence="",
                    )
                )
            else:
                corrected_suggestions.append(suggestion)

        # Rebuild the analysis only if any field was corrected.
        skills_changed = corrected_technical != list(
            analysis.technical_skills
        ) or corrected_soft != list(analysis.soft_skills)
        suggestions_changed = corrected_suggestions != list(analysis.resume_improvements)

        if skills_changed or suggestions_changed:
            analysis = ResumeAnalysis(
                summary=analysis.summary,
                technical_skills=tuple(corrected_technical),
                soft_skills=tuple(corrected_soft),
                experience_assessment=analysis.experience_assessment,
                experience_highlights=analysis.experience_highlights,
                learning_suggestions=analysis.learning_suggestions,
                resume_improvements=tuple(corrected_suggestions),
                caveats=analysis.caveats,
            )

        return analysis
