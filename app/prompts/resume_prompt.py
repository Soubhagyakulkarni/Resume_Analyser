"""Static, reviewed system prompt used for resume analysis."""

from pathlib import Path

_PROMPT_FILE = Path(__file__).resolve().parents[2] / "prompts" / "resume_analysis.txt"


def get_resume_analysis_prompt() -> str:
    """Load the packaged prompt asset without interpolating user-provided text."""
    return _PROMPT_FILE.read_text(encoding="utf-8")
