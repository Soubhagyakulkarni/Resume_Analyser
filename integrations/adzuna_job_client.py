"""Adzuna job search adapter for refreshing the local catalog."""

import json
import logging
import re
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.utils.errors import JobSourceUnavailableError
from models.job import Job
from utils.url_validation import is_placeholder_application_url

logger = logging.getLogger(__name__)
_API_ROOT = "https://api.adzuna.com/v1/api/jobs"
_RESULTS_PER_PAGE = 20
_MAX_RESPONSE_BYTES = 5 * 1024 * 1024
_KNOWN_SKILLS = (
    "Machine Learning",
    "Data Analysis",
    "Project Management",
    "Customer Service",
    "Power BI",
    "JavaScript",
    "TypeScript",
    "Kubernetes",
    "Communication",
    "Leadership",
    "Python",
    "React",
    "Node.js",
    "Django",
    "Flask",
    "FastAPI",
    "Docker",
    "Tableau",
    "Excel",
    "Scrum",
    "Agile",
    "Sales",
    "Marketing",
    "Java",
    "SQL",
    "C++",
    "C#",
    "AWS",
    "Azure",
    "GCP",
    "Git",
    "Linux",
    "HTML",
    "CSS",
    "Go",
    "Rust",
    "Pandas",
    "NumPy",
    "TensorFlow",
    "PyTorch",
    "Spring Boot",
    "REST APIs",
    "PostgreSQL",
    "MongoDB",
    "MySQL",
    "DevOps",
    "CI/CD",
    "Selenium",
    "Testing",
)


class _TextExtractor(HTMLParser):
    """Convert source job-description markup into plain text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = data.strip()
        if cleaned:
            self.parts.append(cleaned)


def _plain_text(value: str, limit: int = 12000) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()[:limit]


def _extract_skills(title: str, description: str) -> tuple[str, ...]:
    source_text = f"{title}\n{description}"
    return tuple(
        skill
        for skill in _KNOWN_SKILLS
        if re.search(
            rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])",
            source_text,
            flags=re.IGNORECASE,
        )
    )


def _listing_date(value: object) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Adzuna listing is missing its creation date")
    cleaned = value.strip()
    try:
        return date.fromisoformat(cleaned)
    except ValueError:
        return datetime.fromisoformat(cleaned).date()


def _to_job(value: object, country_code: str) -> Job:
    if not isinstance(value, dict):
        raise TypeError("Adzuna listing must be an object")
    listing_id = value.get("id")
    title_value = value.get("title")
    description_value = value.get("description", "")
    if not isinstance(listing_id, (str, int)) or not isinstance(title_value, str):
        raise TypeError("Adzuna listing is missing its identifier or title")
    if not isinstance(description_value, str):
        raise TypeError("Adzuna listing description must be text")

    title = _plain_text(title_value, limit=300).replace("**", "").strip()
    description = _plain_text(description_value)
    if not title:
        raise ValueError("Adzuna listing has an empty title")

    location_value = value.get("location")
    location = ""
    if isinstance(location_value, dict):
        display_name = location_value.get("display_name")
        if isinstance(display_name, str):
            location = _plain_text(display_name, limit=300)
    if country_code == "in" and location and "india" not in location.casefold():
        location = f"{location}, India"

    redirect_url = value.get("redirect_url", "")
    application_url = ""
    if (
        isinstance(redirect_url, str)
        and redirect_url.startswith("https://")
        and not is_placeholder_application_url(redirect_url)
    ):
        application_url = redirect_url

    return Job(
        id=f"adzuna-{country_code}-{listing_id}",
        title=title,
        description=description,
        required_skills=_extract_skills(title, description),
        location=location,
        application_url=application_url,
        source="Adzuna",
        updated_at=_listing_date(value.get("created")),
    )


class AdzunaJobClient:
    """Fetch and normalize current job advertisements from the Adzuna API."""

    def __init__(
        self,
        app_id: str | None,
        app_key: str | None,
        country_code: str = "in",
        timeout_seconds: float = 20,
    ) -> None:
        if not app_id or not app_key:
            raise ValueError("ADZUNA_APP_ID and ADZUNA_APP_KEY are required")
        if not re.fullmatch(r"[a-z]{2}", country_code):
            raise ValueError("country_code must be a two-letter lowercase code")
        if not 0 < timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be between 0 and 60")
        self._app_id = app_id
        self._app_key = app_key
        self._country_code = country_code
        self._timeout_seconds = timeout_seconds

    def search(
        self,
        what: str,
        where: str,
        pages: int = 3,
    ) -> list[Job]:
        """Fetch a bounded set of listings; does not modify the local catalog."""
        if not what.strip() or len(what) > 200:
            raise ValueError("what must contain 1 to 200 characters")
        if len(where) > 200:
            raise ValueError("where must be at most 200 characters")
        if not 1 <= pages <= 10:
            raise ValueError("pages must be between 1 and 10")

        jobs_by_id: dict[str, Job] = {}
        for page in range(1, pages + 1):
            payload = self._fetch_page(what.strip(), where.strip(), page)
            results = payload.get("results")
            if not isinstance(results, list):
                logger.warning("Adzuna response omitted a valid results list page=%d", page)
                raise JobSourceUnavailableError() from None
            for record in results:
                try:
                    job = _to_job(record, self._country_code)
                except (TypeError, ValueError):
                    logger.warning("Skipping malformed Adzuna listing page=%d", page)
                    continue
                jobs_by_id[job.id] = job
            if not results:
                break
        return list(jobs_by_id.values())

    def _fetch_page(self, what: str, where: str, page: int) -> dict[str, object]:
        query = urlencode(
            {
                "app_id": self._app_id,
                "app_key": self._app_key,
                "results_per_page": _RESULTS_PER_PAGE,
                "what": what,
                "where": where,
                "content-type": "application/json",
            }
        )
        request = Request(
            f"{_API_ROOT}/{self._country_code}/search/{page}?{query}",
            headers={"Accept": "application/json", "User-Agent": "AIResumeAnalyzer/1.0"},
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                if response.status != 200:
                    logger.warning("Adzuna request returned status_code=%d", response.status)
                    raise JobSourceUnavailableError() from None
                raw_body = response.read(_MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            logger.warning("Adzuna request failed status_code=%d", exc.code)
            raise JobSourceUnavailableError() from None
        except (URLError, TimeoutError, OSError) as exc:
            logger.warning("Adzuna request could not complete error_type=%s", type(exc).__name__)
            raise JobSourceUnavailableError() from None

        if len(raw_body) > _MAX_RESPONSE_BYTES:
            logger.warning("Adzuna response exceeded the configured size limit")
            raise JobSourceUnavailableError() from None
        try:
            payload = json.loads(raw_body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Adzuna returned invalid JSON")
            raise JobSourceUnavailableError() from None
        if not isinstance(payload, dict):
            logger.warning("Adzuna returned an invalid response shape")
            raise JobSourceUnavailableError() from None
        return payload
