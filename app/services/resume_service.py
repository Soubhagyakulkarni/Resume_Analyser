"""Resume input validation and PDF, DOCX, or pasted-text parsing."""

from app.utils.errors import InvalidResumeError
from models.resume import ParsedResume
from parsers.docx_parser import parse_docx
from parsers.file_validator import validate_resume_file
from parsers.pdf_parser import parse_pdf


class ResumeService:
    """Validate resume input and convert it to bounded plain text."""

    def __init__(self, max_upload_bytes: int, max_resume_chars: int = 50_000) -> None:
        self._max_upload_bytes = max_upload_bytes
        self._max_resume_chars = max_resume_chars

    @property
    def max_resume_chars(self) -> int:
        """Maximum extracted or pasted resume length accepted by this service."""
        return self._max_resume_chars

    def parse(self, filename: str, content: bytes) -> ParsedResume:
        """Validate and extract text from a supported resume document."""
        file_type = validate_resume_file(filename, content, self._max_upload_bytes)
        if file_type == "pdf":
            parsed = parse_pdf(filename, content)
        elif file_type == "docx":
            parsed = parse_docx(filename, content)
        else:  # txt
            text = content.decode("utf-8", errors="replace").strip()
            if not text:
                from app.utils.errors import InvalidResumeError
                raise InvalidResumeError("No readable text was found in the TXT file")
            parsed = ParsedResume(filename=filename, file_type="text", text=text)
        self._validate_text_length(parsed.text)
        return parsed

    def parse_text(self, text: str) -> ParsedResume:
        """Validate pasted resume text as UTF-8 text."""
        if not text.strip():
            raise InvalidResumeError("Paste resume text or upload a resume file")
        self._validate_text_length(text)
        return ParsedResume(
            filename="pasted-resume.txt",
            file_type="text",
            text=text.strip(),
        )

    def _validate_text_length(self, text: str) -> None:
        if len(text) > self._max_resume_chars:
            raise InvalidResumeError(
                f"Resume text exceeds the {self._max_resume_chars}-character limit"
            )
