"""Job catalog and recommendation models."""

from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class Job:
    id: str
    title: str
    description: str
    required_skills: tuple[str, ...]
    location: str
    application_url: str
    source: str
    updated_at: date

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.title.strip() or not self.source.strip():
            raise ValueError("A job requires an id, title, and source")
        if self.application_url:
            parsed_url = urlparse(self.application_url)
            if parsed_url.scheme != "https" or not parsed_url.netloc:
                raise ValueError("Job application URLs must use HTTPS")


@dataclass(frozen=True, slots=True)
class JobRecommendation:
    job: Job
    matched_skills: tuple[str, ...]
    missing_from_resume: tuple[str, ...]
    match_ratio: float
    rationale: str
