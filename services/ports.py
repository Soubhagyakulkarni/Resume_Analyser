"""Protocol contracts for external dependencies."""

from typing import Protocol

from models.analysis import ResumeAnalysis
from models.job import Job


class AnalysisGateway(Protocol):
    def analyze(self, resume_text: str) -> ResumeAnalysis: ...


class JobRepository(Protocol):
    def list_active_jobs(self) -> list[Job]: ...
    def replace_jobs(self, jobs: list[Job]) -> None: ...


class PdfRenderer(Protocol):
    def render(self, title: str, sections: list[tuple[str, list[str]]]) -> bytes: ...
