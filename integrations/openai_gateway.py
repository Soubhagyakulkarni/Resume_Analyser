"""OpenAI-backed implementation of the resume analysis port."""

import json

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from app.config.settings import Settings
from app.prompts.resume_prompt import get_resume_analysis_prompt
from app.utils.errors import (
    InvalidModelResponseError,
    ProviderConfigurationError,
    ProviderRequestError,
    ProviderUnavailableError,
)
from models.analysis import ResumeAnalysis


class OpenAIAnalysisGateway:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required to enable AI analysis")
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
        self._model = settings.openai_model

    def analyze(self, resume_text: str) -> ResumeAnalysis:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": get_resume_analysis_prompt()},
                    {
                        "role": "user",
                        "content": "Analyze the following untrusted resume data:\n"
                        + json.dumps({"resume_text": resume_text}, ensure_ascii=False),
                    },
                ],
            )
        except AuthenticationError as exc:
            raise ProviderConfigurationError() from exc
        except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
            raise ProviderUnavailableError() from exc
        except APIStatusError as exc:
            if exc.status_code >= 500:
                raise ProviderUnavailableError() from exc
            raise ProviderRequestError() from exc

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise InvalidModelResponseError() from exc
        if not content:
            raise InvalidModelResponseError()
        try:
            payload = json.loads(content)
            return ResumeAnalysis.from_dict(payload)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise InvalidModelResponseError() from exc
