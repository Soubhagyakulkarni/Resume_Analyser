"""Google Gemini implementation of the resume analysis port."""

import json
import logging
import time

from google import genai
from google.genai import errors, types

from app.config.settings import Settings
from app.prompts.resume_prompt import get_resume_analysis_prompt
from app.utils.errors import (
    InvalidModelResponseError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderUnavailableError,
)
from models.analysis import ResumeAnalysis

logger = logging.getLogger(__name__)


class GeminiAnalysisGateway:
    """Call Gemini for schema-validated, evidence-grounded resume analysis."""

    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")
        self._client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=int(settings.openai_timeout_seconds * 1000)),
        )
        self._model = settings.gemini_model
        self._max_retries = settings.openai_max_retries

    def analyze(self, resume_text: str) -> ResumeAnalysis:
        """Generate analysis and validate all returned fields locally."""
        request_content = json.dumps({"resume_text": resume_text}, ensure_ascii=False)
        models_to_try = [self._model]
        if self._model != "gemini-2.0-flash":
            models_to_try.append("gemini-2.0-flash")

        response = None
        last_exc: Exception | None = None
        for current_model in models_to_try:
            for attempt in range(self._max_retries + 1):
                try:
                    response = self._client.models.generate_content(
                        model=current_model,
                        contents=request_content,
                        config=types.GenerateContentConfig(
                            system_instruction=get_resume_analysis_prompt(),
                            response_mime_type="application/json",
                            temperature=0.2,
                            max_output_tokens=4000,
                        ),
                    )
                    break
                except errors.APIError as exc:
                    last_exc = exc
                    status_code = getattr(exc, "code", None)
                    error_message = str(getattr(exc, "message", "")).casefold()
                    logger.warning(
                        "Gemini request failed model=%s status_code=%s attempt=%d message=%s",
                        current_model,
                        status_code if isinstance(status_code, int) else "unknown",
                        attempt + 1,
                        error_message[:200],
                    )
                    invalid_api_key = status_code == 400 and (
                        "api key" in error_message
                        and ("invalid" in error_message or "not valid" in error_message)
                    )
                    if status_code in {401, 403} or invalid_api_key:
                        raise ProviderConfigurationError() from exc
                    if status_code == 429:
                        raise ProviderRateLimitError() from exc
                    is_server_err = (
                        isinstance(exc, errors.ServerError)
                        or (isinstance(status_code, int) and (status_code >= 500 or status_code == 404))
                        or "overloaded" in error_message
                        or "unavailable" in error_message
                    )
                    if is_server_err:
                        if attempt < self._max_retries:
                            time.sleep(min(2 * (attempt + 1), 6))
                            continue
                        break
                    raise ProviderRequestError() from exc
                except (OSError, RuntimeError, ValueError) as exc:
                    last_exc = exc
                    logger.warning(
                        "Gemini network error model=%s attempt=%d error=%s",
                        current_model,
                        attempt + 1,
                        type(exc).__name__,
                    )
                    if attempt < self._max_retries:
                        time.sleep(min(2**attempt, 2))
                        continue
                    break

            if response is not None:
                break

        if response is None:
            raise ProviderUnavailableError() from last_exc


        content = getattr(response, "text", None)
        if not isinstance(content, str) or not content.strip():
            raise InvalidModelResponseError()
        try:
            payload = json.loads(content)
            return ResumeAnalysis.from_dict(payload)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise InvalidModelResponseError() from exc

    def extract_text_from_pdf(self, content: bytes) -> str:
        """Extract plain text from scanned or image-based PDF using Gemini multimodal."""
        # shortcut: inline PDF bytes capped at 4000 output tokens, upgrade to File API for 20+ page docs
        prompt = (
            "Extract all readable text from this scanned resume document accurately and completely. "
            "Preserve sections, headings, bullet points, skills, contact info, and dates as plain text. "
            "Return only the extracted text without commentary."
        )
        pdf_part = types.Part.from_bytes(data=content, mime_type="application/pdf")
        models_to_try = [self._model]
        if self._model != "gemini-2.0-flash":
            models_to_try.append("gemini-2.0-flash")

        for current_model in models_to_try:
            for attempt in range(self._max_retries + 1):
                try:
                    response = self._client.models.generate_content(
                        model=current_model,
                        contents=[pdf_part, prompt],
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=4000,
                        ),
                    )
                    text = getattr(response, "text", "") or ""
                    if text.strip():
                        return text.strip()
                except (errors.APIError, OSError, ValueError, RuntimeError) as exc:
                    logger.warning(
                        "Gemini PDF OCR attempt failed model=%s attempt=%d error=%s",
                        current_model,
                        attempt + 1,
                        exc,
                    )
                    if attempt < self._max_retries:
                        time.sleep(1)
                        continue
                    break
        return ""

    def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector embedding using gemini-embedding-001."""
        # shortcut: truncated to 4000 chars for single-call embedding, upgrade for book-length documents
        clean_text = text[:4000].strip()
        if not clean_text:
            return []
        try:
            response = self._client.models.embed_content(
                model="gemini-embedding-001",
                contents=clean_text,
            )
            if response.embeddings and response.embeddings[0].values:
                return list(response.embeddings[0].values)
        except (errors.APIError, OSError, ValueError, RuntimeError) as exc:
            logger.warning("Gemini text embedding failed: %s", exc)
        return []
