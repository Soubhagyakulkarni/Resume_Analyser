"""Server-side validation for supported resume uploads."""

from io import BytesIO
from pathlib import PurePath
from zipfile import BadZipFile, ZipFile

from app.utils.errors import InvalidResumeError

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_DOCX_ARCHIVE_ENTRIES = 1_000


def validate_resume_file(filename: str, content: bytes, max_bytes: int) -> str:
    if not filename or not content:
        raise InvalidResumeError("The uploaded file is empty")
    if len(content) > max_bytes:
        raise InvalidResumeError("The uploaded file exceeds the size limit")
    extension = PurePath(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise InvalidResumeError("Only PDF, DOCX, and TXT resumes are supported")
    if extension == ".pdf" and b"%PDF-" not in content[:1024]:
        raise InvalidResumeError("The file does not contain a valid PDF signature")
    if extension == ".docx":
        try:
            with ZipFile(BytesIO(content)) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_DOCX_ARCHIVE_ENTRIES:
                    raise InvalidResumeError("The DOCX archive contains too many entries")
                if sum(entry.file_size for entry in entries) > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise InvalidResumeError("The DOCX expands beyond the supported size limit")
                if "word/document.xml" not in {entry.filename for entry in entries}:
                    raise InvalidResumeError("The DOCX document is missing its main content")
        except (BadZipFile, OSError) as exc:
            raise InvalidResumeError("The DOCX file is corrupted") from exc
    return extension[1:]
