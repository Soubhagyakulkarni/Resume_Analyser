"""Import an authorized CSV job catalog into the SQLite catalog."""

import argparse
import csv
import logging
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from config.logging_config import configure_logging
from config.settings import Settings
from models.job import Job
from repositories.sqlite_job_repository import SQLiteJobRepository
from utils.url_validation import is_placeholder_application_url

REQUIRED_COLUMNS = {
    "id",
    "title",
    "description",
    "required_skills",
    "location",
    "application_url",
    "source",
    "updated_at",
}


def load_jobs(csv_path: Path) -> list[Job]:
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(f"CSV must include columns: {', '.join(sorted(REQUIRED_COLUMNS))}")
        jobs: list[Job] = []
        seen_ids: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            job_id = row["id"].strip()
            title = row["title"].strip()
            source = row["source"].strip()
            skills = tuple(
                value.strip() for value in row["required_skills"].split("|") if value.strip()
            )
            application_url = row["application_url"].strip()
            if not job_id or not title or not source or not skills:
                raise ValueError(f"CSV row {line_number} is missing a required value")
            if job_id in seen_ids:
                raise ValueError(f"CSV row {line_number} duplicates job id {job_id!r}")
            if application_url:
                parsed_url = urlparse(application_url)
                if parsed_url.scheme != "https" or not parsed_url.netloc:
                    raise ValueError(f"CSV row {line_number} has a non-HTTPS application URL")
                if is_placeholder_application_url(application_url):
                    raise ValueError(f"CSV row {line_number} uses a placeholder application domain")
            try:
                updated_at = date.fromisoformat(row["updated_at"].strip())
            except ValueError as exc:
                raise ValueError(f"CSV row {line_number} has an invalid ISO date") from exc
            jobs.append(
                Job(
                    id=job_id,
                    title=title,
                    description=row["description"].strip(),
                    required_skills=skills,
                    location=row["location"].strip(),
                    application_url=application_url,
                    source=source,
                    updated_at=updated_at,
                )
            )
            seen_ids.add(job_id)
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="CSV from an authorized job data source")
    args = parser.parse_args()
    configure_logging()
    settings = Settings.from_environment()
    jobs = load_jobs(args.csv_file)
    SQLiteJobRepository(settings.sqlite_database_path).replace_jobs(jobs)
    logging.getLogger(__name__).info("Imported %d authorized job listings", len(jobs))


if __name__ == "__main__":
    main()
