"""Text extraction for PDF resumes."""

import logging
from collections.abc import Callable
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.utils.errors import InvalidResumeError
from models.resume import ParsedResume

logger = logging.getLogger(__name__)

MAX_PDF_PAGES = 100


def parse_pdf(
    filename: str,
    content: bytes,
    ocr_fallback: Callable[[bytes], str] | None = None,
) -> ParsedResume:
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted:
            raise InvalidResumeError("Password-protected PDFs are not supported")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise InvalidResumeError(f"PDF resumes may not exceed {MAX_PDF_PAGES} pages")
        page_texts: list[str] = []
        for page in reader.pages:
            try:
                extracted = page.extract_text()
                if extracted:
                    page_texts.append(extracted)
            except (PdfReadError, ValueError, KeyError, OSError) as exc:
                logger.debug("Failed extracting page text: %s", exc)
                continue
        text = "\n".join(page_texts).strip()
    except InvalidResumeError:
        raise
    except (PdfReadError, ValueError, KeyError, OSError) as exc:
        raise InvalidResumeError("The PDF could not be parsed") from exc

    # If text is empty or sparse (e.g. scanned image), try multimodal OCR fallback
    if len(text) < 50 and ocr_fallback is not None:
        try:
            ocr_text = (ocr_fallback(content) or "").strip()
            if len(ocr_text) > len(text):
                text = ocr_text
        except (InvalidResumeError, RuntimeError, ValueError, OSError) as exc:
            logger.debug("OCR fallback failed: %s", exc)

    if not text:
        raise InvalidResumeError("No readable text was found in the PDF")
    return ParsedResume(filename=filename, file_type="pdf", text=text)
