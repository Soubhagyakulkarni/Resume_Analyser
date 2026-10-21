"""Compatibility prompt-loader import."""

from app.prompts.resume_prompt import get_resume_analysis_prompt


def load_resume_analysis_prompt() -> str:
    return get_resume_analysis_prompt()
