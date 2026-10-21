"""Validated settings and local .env loading for the application."""

import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _get_config(key: str, default: str | None = None) -> str | None:
    """Read a setting from environment variables, falling back to Streamlit secrets."""
    val = os.getenv(key)
    if val is not None:
        return val
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            sec_val = st.secrets[key]
            if sec_val is not None:
                return str(sec_val)
    except Exception:
        pass
    return default


@dataclass(frozen=True, slots=True)
class Settings:
    ai_provider: str
    openai_api_key: str | None
    openai_model: str
    gemini_api_key: str | None
    gemini_model: str
    openai_timeout_seconds: float
    openai_max_retries: int
    max_upload_bytes: int
    max_resume_chars: int
    sqlite_database_path: Path
    job_listing_max_age_days: int
    adzuna_app_id: str | None
    adzuna_app_key: str | None
    adzuna_country_code: str
    log_level: str
    sqlite_user_database_path: Path = Path(PROJECT_ROOT / "data" / "users.sqlite3")

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load settings and reject malformed operational limits."""
        timeout_str = _get_config("OPENAI_TIMEOUT_SECONDS", "45")
        retries_str = _get_config("OPENAI_MAX_RETRIES", "3")
        upload_limit_str = _get_config("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))
        text_limit_str = _get_config("MAX_RESUME_CHARS", "50000")
        job_max_age_str = _get_config("JOB_LISTING_MAX_AGE_DAYS", "30")
        country_str = _get_config("ADZUNA_COUNTRY_CODE", "in")

        timeout = float(timeout_str if timeout_str is not None else "45")
        retries = int(retries_str if retries_str is not None else "3")
        upload_limit = int(upload_limit_str if upload_limit_str is not None else str(10 * 1024 * 1024))
        text_limit = int(text_limit_str if text_limit_str is not None else "50000")
        job_max_age = int(job_max_age_str if job_max_age_str is not None else "30")
        adzuna_country_code = (country_str or "in").strip().lower()

        provider_val = _get_config("AI_PROVIDER")
        if provider_val is not None:
            provider = provider_val.strip().lower()
            if provider not in {"openai", "gemini"}:
                raise ValueError("AI_PROVIDER must be either 'openai' or 'gemini'")
        else:
            provider = "openai"

        model_val = _get_config("OPENAI_MODEL")
        model = model_val.strip() if model_val is not None else "gpt-4o-mini"
        if not model:
            raise ValueError("OPENAI_MODEL must not be empty")

        gemini_model_val = _get_config("GEMINI_MODEL")
        gemini_model = gemini_model_val.strip() if gemini_model_val is not None else "gemini-2.0-flash"
        if not gemini_model:
            raise ValueError("GEMINI_MODEL must not be empty")
        if gemini_model in {"gemini-3.5-flash", "gemini-3.8-flash"}:
            gemini_model = "gemini-2.0-flash"

        if not math.isfinite(timeout) or timeout <= 0 or timeout > 300:
            raise ValueError("OPENAI_TIMEOUT_SECONDS must be between 0 and 300")
        if not 0 <= retries <= 3:
            raise ValueError("OPENAI_MAX_RETRIES must be between 0 and 3")
        if not 0 < upload_limit <= 10 * 1024 * 1024:
            raise ValueError("MAX_UPLOAD_BYTES must be between 1 and 10485760")
        if not 0 < text_limit <= 200_000:
            raise ValueError("MAX_RESUME_CHARS must be between 1 and 200000")
        if not 1 <= job_max_age <= 365:
            raise ValueError("JOB_LISTING_MAX_AGE_DAYS must be between 1 and 365")
        if not re.fullmatch(r"[a-z]{2}", adzuna_country_code):
            raise ValueError("ADZUNA_COUNTRY_CODE must be a two-letter country code")

        database_path = Path(
            _get_config("SQLITE_DATABASE_PATH", str(PROJECT_ROOT / "data" / "jobs.sqlite3")) or ""
        ).expanduser()
        user_database_path = Path(
            _get_config("SQLITE_USER_DATABASE_PATH", str(PROJECT_ROOT / "data" / "users.sqlite3")) or ""
        ).expanduser()

        openai_key = (_get_config("OPENAI_API_KEY") or "").strip() or None
        gemini_key = (_get_config("GEMINI_API_KEY") or "").strip() or None
        adzuna_id = (_get_config("ADZUNA_APP_ID") or "").strip() or None
        adzuna_key = (_get_config("ADZUNA_APP_KEY") or "").strip() or None
        log_level = (_get_config("LOG_LEVEL", "INFO") or "INFO").strip().upper()

        return cls(
            ai_provider=provider,
            openai_api_key=openai_key,
            openai_model=model,
            gemini_api_key=gemini_key,
            gemini_model=gemini_model,
            openai_timeout_seconds=timeout,
            openai_max_retries=retries,
            max_upload_bytes=upload_limit,
            max_resume_chars=text_limit,
            sqlite_database_path=database_path,
            job_listing_max_age_days=job_max_age,
            adzuna_app_id=adzuna_id,
            adzuna_app_key=adzuna_key,
            adzuna_country_code=adzuna_country_code,
            log_level=log_level,
            sqlite_user_database_path=user_database_path,
        )
