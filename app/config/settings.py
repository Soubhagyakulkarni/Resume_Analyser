"""Validated settings and local .env loading for the application."""

import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)


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
        timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
        retries = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
        upload_limit = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
        text_limit = int(os.getenv("MAX_RESUME_CHARS", "50000"))
        job_max_age = int(os.getenv("JOB_LISTING_MAX_AGE_DAYS", "30"))
        adzuna_country_code = os.getenv("ADZUNA_COUNTRY_CODE", "in").strip().lower()
        provider = os.getenv("AI_PROVIDER", "openai").strip().lower()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
        if provider not in {"openai", "gemini"}:
            raise ValueError("AI_PROVIDER must be either 'openai' or 'gemini'")
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
        if not model:
            raise ValueError("OPENAI_MODEL must not be empty")
        if not gemini_model:
            raise ValueError("GEMINI_MODEL must not be empty")

        database_path = Path(
            os.getenv("SQLITE_DATABASE_PATH", str(PROJECT_ROOT / "data" / "jobs.sqlite3"))
        ).expanduser()
        user_database_path = Path(
            os.getenv("SQLITE_USER_DATABASE_PATH", str(PROJECT_ROOT / "data" / "users.sqlite3"))
        ).expanduser()
        return cls(
            ai_provider=provider,
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip() or None,
            openai_model=model,
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip() or None,
            gemini_model=gemini_model,
            openai_timeout_seconds=timeout,
            openai_max_retries=retries,
            max_upload_bytes=upload_limit,
            max_resume_chars=text_limit,
            sqlite_database_path=database_path,
            job_listing_max_age_days=job_max_age,
            adzuna_app_id=os.getenv("ADZUNA_APP_ID", "").strip() or None,
            adzuna_app_key=os.getenv("ADZUNA_APP_KEY", "").strip() or None,
            adzuna_country_code=adzuna_country_code,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            sqlite_user_database_path=user_database_path,
        )
